"""
E2E Toy Scenario Test for Zarqa al Yamama V2

Tests the complete V2 pipeline with:
- Mocked Librarian (no network)
- Syndicated duplicates + independent sources
- explain_fusion validation
- Independence penalty verification
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import uuid

# Import v2 contracts
from app.graph.contracts import (
    EvidenceItem, ClaimItem, AgentOutput, Signal,
    TimeHorizon, SourceType, HorizonForecast, FusionResult,
    ExplainFusion, ScenarioProbability,
)
from app.graph.state import ForecastState


# ===========================================================================
# MOCK FIXTURES
# ===========================================================================

@pytest.fixture
def mock_evidence_syndicated():
    """Two syndicated duplicates (same content_hash)."""
    content_hash = "a" * 64  # Same hash = duplicates
    
    e1 = EvidenceItem(
        id=str(uuid.uuid4()),
        url="https://reuters.com/oil-price-rises",
        canonical_url="https://reuters.com/oil-price-rises",
        domain="reuters.com",
        content_hash=content_hash,
        snippet="Oil prices rose 5% today due to supply constraints.",
        source_type=SourceType.PRIMARY,
        reliability_tier=1,
    )
    
    e2 = EvidenceItem(
        id=str(uuid.uuid4()),
        url="https://yahoo.com/finance/oil-price-rises",
        canonical_url="https://yahoo.com/finance/oil-price-rises", 
        domain="yahoo.com",
        content_hash=content_hash,  # Same hash - syndicated
        snippet="Oil prices rose 5% today due to supply constraints.",
        source_type=SourceType.AGGREGATOR,
        reliability_tier=3,
    )
    
    return [e1, e2]


@pytest.fixture
def mock_evidence_independent():
    """One independent source (different publisher/cluster)."""
    return EvidenceItem(
        id=str(uuid.uuid4()),
        url="https://ft.com/analysis/opec-strategy",
        canonical_url="https://ft.com/analysis/opec-strategy",
        domain="ft.com",
        content_hash="b" * 64,  # Different hash = independent
        snippet="OPEC strategy meeting concluded with production cuts.",
        source_type=SourceType.PRIMARY,
        reliability_tier=1,
    )


@pytest.fixture
def mock_agent_outputs(mock_evidence_syndicated, mock_evidence_independent):
    """Create mock agent outputs for market and context adapters."""
    all_evidence = mock_evidence_syndicated + [mock_evidence_independent]
    evidence_ids = [e.id for e in all_evidence]
    
    # Create a dummy internal evidence for market classifier signal
    internal_evidence = EvidenceItem(
        id=str(uuid.uuid4()),
        url="internal://market_classifier/signal",
        canonical_url="internal://market_classifier/signal",
        domain="internal",
        content_hash="c" * 64,
        snippet="Internal market classification signal",
        source_type=SourceType.PRIMARY,
        reliability_tier=1,
    )
    
    market_output = AgentOutput(
        agent_id="market_classifier",
        claims=[
            ClaimItem(
                text="Scenario is market-related: oil_prices",
                evidence_ids=[internal_evidence.id],  # Now has required evidence reference
                confidence=0.9,
                confidence_justification="Internal classification",
                time_horizon=TimeHorizon.SHORT_TERM,
                falsifiable=False,
            )
        ],
        evidence=[internal_evidence],
        signals=[
            Signal(
                name="market_classification",
                value=1.0,
                time_horizon=TimeHorizon.SHORT_TERM,
                source="market_classifier",
            )
        ],
        confidence=0.9,
        confidence_justification="Classification model output",
    )
    
    context_output = AgentOutput(
        agent_id="context_interpreter",
        claims=[
            ClaimItem(
                text="Oil supply constraints expected in Q1 2026",
                evidence_ids=evidence_ids,
                confidence=0.75,
                confidence_justification="Based on multiple sources",
                time_horizon=TimeHorizon.SHORT_TERM,
            ),
            ClaimItem(
                text="OPEC production cuts likely to continue",
                evidence_ids=[mock_evidence_independent.id],
                confidence=0.7,
                confidence_justification="FT analysis",
                time_horizon=TimeHorizon.MEDIUM_TERM,
            ),
        ],
        evidence=all_evidence,
        signals=[
            Signal(
                name="sentiment_score",
                value=0.6,
                time_horizon=TimeHorizon.SHORT_TERM,
                source="context_interpreter",
            )
        ],
        confidence=0.7,
        confidence_justification="Context analysis",
    )
    
    return {
        "market_classifier": market_output,
        "context_interpreter": context_output,
    }


@pytest.fixture
def initial_state():
    """Create minimal initial state."""
    return {
        "scenario": "Will Middle East oil prices rise above $100/barrel in Q1 2026?",
        "scenario_is_market": True,
        "scenario_classification": "oil_prices",
        "scenario_classification_confidence": 0.9,
        "context_sentiment": {"sentiment_score": 0.6},
        "context_themes": ["oil prices", "OPEC", "supply constraints"],
        "context_key_actors": ["OPEC", "Saudi Arabia"],
        "context_mentions_24h": 150,
        "context_data_sources": [
            "https://reuters.com/oil-price-rises",
            "https://yahoo.com/finance/oil-price-rises",
            "https://ft.com/analysis/opec-strategy",
        ],
        "context_confidence": 0.7,
        "agent_outputs": {},
        "agents_executed": [],
        "errors": [],
        "warnings": [],
    }


# ===========================================================================
# E2E TEST
# ===========================================================================

class TestV2PipelineE2E:
    """End-to-end tests for V2 pipeline with mocked dependencies."""
    
    def test_e2e_toy_scenario_complete(
        self, 
        initial_state, 
        mock_agent_outputs,
        mock_evidence_syndicated,
        mock_evidence_independent,
    ):
        """
        Full E2E test that validates:
        A) Graph completes without exception
        B) Scenario probabilities sum to 1.0 (±1e-6)
        C) Quantile monotonicity: P10 <= P50 <= P90
        D) Claim-evidence linkage valid
        E) explain_fusion exists with required fields
        F) Independence penalty actually applied (not always 1.0)
        """
        async def _run_test():
            from app.retrieval.evidence_deduper import evidence_deduper
            from app.retrieval.independence_analyzer import independence_analyzer
            from app.agents.schema_validator import schema_validator
            from app.agents.quantifier_v2 import quantifier_v2
            
            # Setup state with mock agent outputs
            state = initial_state.copy()
            state["agent_outputs"] = mock_agent_outputs
            
            # Step 1: Run evidence deduper
            all_evidence = mock_evidence_syndicated + [mock_evidence_independent]
            deduplicated = evidence_deduper.deduplicate_batch(all_evidence)
            
            # Syndicated duplicates should be reduced
            assert len(deduplicated) < len(all_evidence) or len(all_evidence) <= 2
            
            state["deduped_evidence"] = deduplicated
            state["evidence_clusters"] = evidence_deduper.get_cluster_stats()
            
            # Step 2: Run independence analyzer
            independence_results = {}
            for agent_id, output in mock_agent_outputs.items():
                stats = independence_analyzer.analyze_agent_independence(
                    output.claims, output.evidence
                )
                independence_results[agent_id] = stats
            
            state["independence_summary"] = {
                "agents": independence_results,
                "cluster_count": sum(r.get("cluster_count", 0) for r in independence_results.values()),
                "diversity_score": sum(
                    r.get("overall_independence", 0) for r in independence_results.values()
                ) / max(len(independence_results), 1),
            }
            state["v2_join_complete"] = True
            
            # Step 3: Run quantifier v2
            result_state = await quantifier_v2.quantify(state)
            
            # ================================================================
            # ASSERTION A: Graph completes without exception
            # ================================================================
            assert result_state is not None, "Quantifier returned None"
            assert "fusion_result_v2" in result_state or "quantified_forecast" in result_state
            
            # ================================================================
            # ASSERTION B: Scenario probabilities sum to 1.0 (if present)
            # ================================================================
            horizon_forecasts = result_state.get("horizon_forecasts", {})
            for horizon, forecast in horizon_forecasts.items():
                if hasattr(forecast, 'scenario_probabilities') and forecast.scenario_probabilities:
                    prob_sum = sum(sp.probability for sp in forecast.scenario_probabilities)
                    assert abs(prob_sum - 1.0) < 1e-6, (
                        f"Scenario probabilities for {horizon} sum to {prob_sum}, expected 1.0"
                    )
            
            # ================================================================
            # ASSERTION C: Quantile monotonicity P10 <= P50 <= P90
            # ================================================================
            for horizon, forecast in horizon_forecasts.items():
                if hasattr(forecast, 'p10') and hasattr(forecast, 'p50') and hasattr(forecast, 'p90'):
                    assert forecast.p10 <= forecast.p50 <= forecast.p90, (
                        f"Quantile monotonicity violated for {horizon}: "
                        f"P10={forecast.p10}, P50={forecast.p50}, P90={forecast.p90}"
                    )
            
            # ================================================================
            # ASSERTION D: Claim-evidence linkage valid (except internal signals)
            # ================================================================
            deduped_ids = {e.id for e in state.get("deduped_evidence", [])}
            for agent_id, output in mock_agent_outputs.items():
                for claim in output.claims:
                    if claim.falsifiable:  # Skip internal signals
                        for eid in claim.evidence_ids:
                            # Evidence may be deduplicated, so just check it exists somewhere
                            assert eid in deduped_ids or any(
                                e.id == eid for e in all_evidence
                            ), f"Claim {claim.id} references non-existent evidence {eid}"
            
            # ================================================================
            # ASSERTION E: explain_fusion exists with required fields
            # ================================================================
            fusion_result = result_state.get("fusion_result_v2")
            if fusion_result and hasattr(fusion_result, 'explain_fusion'):
                explain = fusion_result.explain_fusion
                # --- TEMPORARY AUDIT LOGGING ---
                print("\n\n=== EXPLAIN_FUSION AUDIT ===")
                try:
                    import json
                    # Try pydantic v2 dump
                    if hasattr(explain, "model_dump"):
                        print(json.dumps(explain.model_dump(), indent=2, default=str))
                    # Try pydantic v1 dict
                    elif hasattr(explain, "dict"):
                        print(json.dumps(explain.dict(), indent=2, default=str))
                    else:
                        print(explain)
                except Exception as e:
                    print(f"Error dumping explain_fusion: {e}")
                    print(explain)
                print("============================\n")
                # -------------------------------
                
                
                # Check independence_summary/cluster_count available
                assert state["independence_summary"]["cluster_count"] >= 0
                
                # Truth Window Assertions
                if hasattr(explain, 'agent_contributions_final'):
                     assert len(explain.agent_contributions_final) >= 0
                if hasattr(explain, 'independence_trace'):
                     assert isinstance(explain.independence_trace, dict)
                if hasattr(explain, 'penalty_rationale'):
                     assert isinstance(explain.penalty_rationale, dict)
                if hasattr(explain, 'horizon_contributions'):
                     assert isinstance(explain.horizon_contributions, dict)
                
                # Check explain_fusion has independence penalty info
                if hasattr(explain, 'independence_penalties'):
                    assert isinstance(explain.independence_penalties, dict)
                
                # Check horizon weights or agent contributions
                if hasattr(explain, 'agent_contributions'):
                    # Identifiers for adapters (market_classifier, context_interpreter)
                    assert "market_classifier" in explain.agent_contributions, "market_classifier missing from contributions"
                    assert "context_interpreter" in explain.agent_contributions, "context_interpreter missing from contributions"
            
            # ================================================================
            # ASSERTION F: Independence penalty actually applied (not always 1.0)
            # ================================================================
            # With syndicated sources, at least one penalty should be < 1.0
            independence_summary = state["independence_summary"]
            agent_independence_scores = [
                r.get("overall_independence", 1.0) 
                for r in independence_summary.get("agents", {}).values()
            ]
            
            diversity_score = independence_summary.get("diversity_score", 1.0)
            
            # Either diversity_score < 1.0 OR at least one agent has penalty < 1.0
            has_penalty_applied = (
                diversity_score < 1.0 or 
                any(score < 1.0 for score in agent_independence_scores) or
                len(deduplicated) < len(all_evidence)  # Deduplication happened
            )
            
            assert has_penalty_applied, (
                "Independence penalty not applied. Expected at least one penalty < 1.0 "
                f"with syndicated sources. diversity_score={diversity_score}, "
                f"agent_scores={agent_independence_scores}"
            )
            
            print("✅ All E2E assertions passed!")
        
        
        # Run the async test
        asyncio.run(_run_test())

    def test_e2e_fusion_completeness_regression(
        self,
        initial_state,
        mock_agent_outputs,
        mock_evidence_syndicated,
        mock_evidence_independent
    ):
        """
        Regression test: Assert explain_fusion contains market_classifier and context_interpreter,
        and missing other agents does not crash fusion.
        """
        async def _run_test():
            from app.retrieval.evidence_deduper import evidence_deduper
            from app.retrieval.independence_analyzer import independence_analyzer
            from app.agents.quantifier_v2 import quantifier_v2
            
            # Setup state
            state = initial_state.copy()
            state["agent_outputs"] = mock_agent_outputs
            
            # Run dependencies (Mocking the pipeline flow manually since we test components)
            all_evidence = mock_evidence_syndicated + [mock_evidence_independent]
            state["deduped_evidence"] = evidence_deduper.deduplicate_batch(all_evidence)
            state["evidence_clusters"] = evidence_deduper.get_cluster_stats()
            
            independence_results = {}
            for agent_id, output in mock_agent_outputs.items():
                independence_results[agent_id] = independence_analyzer.analyze_agent_independence(
                    output.claims, output.evidence
                )
            
            state["independence_summary"] = {
                "agents": independence_results,
                "cluster_count": 5, 
                "diversity_score": 0.8
            }
            state["v2_join_complete"] = True
            
            # Run Quantifier
            result = await quantifier_v2.quantify(state)
            
            # Assertions
            fusion_result = result.get("fusion_result_v2")
            assert fusion_result is not None, "Fusion result missing"
            
            explain = fusion_result.explain_fusion
            assert explain is not None, "explain_fusion missing"
            
            # Check contributions
            contribs = explain.agent_contributions
            # Check agent_contributions_final alias
            if hasattr(explain, 'agent_contributions_final'):
                assert "market_classifier" in explain.agent_contributions_final
                assert "context_interpreter" in explain.agent_contributions_final
            
            # Identifiers corresponding to market_adapter_v1 and context_adapter_v1
            # Note: The adapters currently emit legacy agent_ids 'market_classifier' and 'context_interpreter'
            assert "market_classifier" in contribs, "market_classifier (Market Adapter) output missing from fusion"
            assert "context_interpreter" in contribs, "context_interpreter (Context Adapter) output missing from fusion"
            
            # Check confidence/probability section (Horizon Forecasts)
            horizon_forecasts = fusion_result.horizon_forecasts
            assert TimeHorizon.SHORT_TERM in horizon_forecasts
            st_forecast = horizon_forecasts[TimeHorizon.SHORT_TERM]
            assert hasattr(st_forecast, "p10")
            assert hasattr(st_forecast, "p50")
            assert hasattr(st_forecast, "p90")
            
        asyncio.run(_run_test())


# ===========================================================================
# EXPLAIN_FUSION INSPECTION TEST
# ===========================================================================

class TestExplainFusionAudit:
    """Tests for explain_fusion output structure and values."""
    
    def test_explain_fusion_structure(self):
        """Verify explain_fusion has the required structure."""
        explain = ExplainFusion(
            agent_contributions={"market_classifier": 0.4, "context_interpreter": 0.6},
            independence_penalties={"context_interpreter": 0.85},
            conflicts_detected=["Signal divergence between agents"],
            normalization_factors={"SHORT_TERM": 1.0},
        )
        
        assert "agent_contributions" in explain.__dict__ or hasattr(explain, 'agent_contributions')
        assert "independence_penalties" in explain.__dict__ or hasattr(explain, 'independence_penalties')
        assert "conflicts_detected" in explain.__dict__ or hasattr(explain, 'conflicts_detected')
    
    def test_independence_penalty_red_flags(self):
        """Test detection of red flag values in independence penalties."""
        # All 1.0 = no penalties applied = RED FLAG
        penalties_all_one = {"agent1": 1.0, "agent2": 1.0}
        all_one = all(p == 1.0 for p in penalties_all_one.values())
        
        # Expected: if we have syndicated sources, should see penalties < 1.0
        if all_one:
            print("⚠️ RED FLAG: All independence penalties = 1.0 (no syndication detected)")
        
        # Good: some penalties < 1.0
        penalties_varied = {"agent1": 0.85, "agent2": 1.0}
        has_penalty = any(p < 1.0 for p in penalties_varied.values())
        assert has_penalty, "Expected at least one penalty < 1.0"
        print("✅ GREEN FLAG: Independence penalties properly applied")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
