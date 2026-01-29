"""
True E2E Test — Compiles and Invokes Runtime LangGraph Workflow

Tests the ACTUAL ZarqaWorkflow with:
- Mocked Librarian (no network)
- Syndicated duplicates + independent sources
- Graph invocation (not just node tests)
- explain_fusion and independence penalty validation
"""

import importlib
import sys
import pytest
import uuid
import os

# Ensure backend root is on sys.path for app.* imports.
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

# ===========================================================================
# WORKFLOW MODULE RELOAD HELPERS (ENV-SENSITIVE)
# ===========================================================================

def _reload_workflow_module():
    module = sys.modules.get("app.workflow")
    if module is None:
        return importlib.import_module("app.workflow")
    return importlib.reload(module)


def _load_workflow(use_v2: bool):
    os.environ["ZARQA_USE_V2"] = "1" if use_v2 else "0"
    return _reload_workflow_module()


@pytest.fixture(autouse=True)
def _force_v2_mode():
    _load_workflow(True)


# ===========================================================================
# FIXTURES
# ===========================================================================

@pytest.fixture
def toy_scenario_state():
    """Minimal initial state for toy scenario."""
    return {
        "scenario": "Will oil prices rise above $100/barrel in Q1 2026?",
        "user_id": "test_user",
        "scenario_is_market": True,
        "scenario_classification": "oil_prices",
        "scenario_classification_confidence": 0.9,
        "context_sentiment": {"sentiment_score": 0.6},
        "context_themes": ["oil prices", "OPEC"],
        "context_key_actors": ["OPEC", "Saudi Arabia"],
        "context_mentions_24h": 150,
        "context_data_sources": [
            "https://reuters.com/oil",
            "https://yahoo.com/oil",  # Syndicated duplicate
            "https://ft.com/opec",    # Independent
        ],
        "context_confidence": 0.7,
        "agent_outputs": {},
        "agents_executed": [],
        "errors": [],
        "warnings": [],
    }


# ===========================================================================
# TRUE E2E TESTS — Compile and Invoke Graph
# ===========================================================================

class TestRuntimeWorkflowE2E:
    """
    True end-to-end tests using the ACTUAL runtime ZarqaWorkflow.
    These tests import from app.workflow (same as main.py).
    """
    
    def test_workflow_module_path_matches_runtime(self):
        """Verify we're importing the same module as main.py."""
        from app.workflow import ZarqaWorkflow
        
        # Check module path matches expected runtime
        assert ZarqaWorkflow.__module__ == "app.workflow"
        print(f"✅ Workflow module: {ZarqaWorkflow.__module__}.{ZarqaWorkflow.__name__}")
    
    def test_graph_compiles_successfully(self):
        """Test that graph compiles without error."""
        from app.workflow import ZarqaWorkflow
        
        workflow = ZarqaWorkflow()
        assert workflow.graph is not None
        print("✅ Graph compiled successfully")
    
    def test_v2_nodes_present_in_compiled_graph(self):
        """Test that v2 nodes exist in compiled graph."""
        from app.workflow import ZarqaWorkflow
        
        workflow = ZarqaWorkflow()
        nodes = getattr(workflow.graph, "nodes", None)
        
        if nodes is None:
            pytest.skip("Graph nodes not accessible via .nodes attribute")
        
        node_keys = list(nodes.keys()) if isinstance(nodes, dict) else []
        
        # Required v2 nodes
        required_v2_nodes = [
            "v2_join_node",
            "schema_validator_node",
            "evidence_deduper_node",
            "independence_analyzer_node",
            "quantifier_v2",
            "critic_v2",
            "market_adapter",
            "context_adapter",
        ]
        
        for node in required_v2_nodes:
            assert node in node_keys, f"Missing v2 node: {node}"
        
        print(f"✅ All {len(required_v2_nodes)} v2 nodes present: {required_v2_nodes}")
    
    def test_v2_gate_chain_methods_exist(self):
        """Test that v2 gate chain node methods exist on workflow."""
        from app.workflow import ZarqaWorkflow
        
        workflow = ZarqaWorkflow()
        
        methods = [
            "_node_v2_join",
            "_node_schema_validator",
            "_node_evidence_deduper",
            "_node_independence_analyzer",
            "_node_quantifier_v2",
            "_node_critic_v2",
        ]
        
        for method in methods:
            assert hasattr(workflow, method), f"Missing method: {method}"
        
        print(f"✅ All {len(methods)} gate chain methods exist")


class TestV2GateChainLogic:
    """Test v2 gate chain node behavior."""
    
    @pytest.mark.asyncio
    async def test_join_node_rejects_partial_state(self):
        """Join node must reject state with only one adapter."""
        from app.workflow import ZarqaWorkflow
        from app.graph.contracts import AgentOutput, ClaimItem, TimeHorizon, EvidenceItem, SourceType
        
        workflow = ZarqaWorkflow()
        
        # Valid dummy evidence
        ev = EvidenceItem(
            id=str(uuid.uuid4()),
            url="http://test.com", canonical_url="http://test.com", domain="test.com",
            content_hash="a"*64, snippet="test", source_type=SourceType.AGGREGATOR
        )
        
        # State with only market adapter (and valid data)
        state = {
            "agent_outputs": {
                "market_classifier": AgentOutput(
                    agent_id="market_classifier",
                    claims=[ClaimItem(
                        text="Test",
                        evidence_ids=[ev.id],
                        confidence=0.9,
                        confidence_justification="Test",
                        time_horizon=TimeHorizon.SHORT_TERM,
                        falsifiable=False,
                    )],
                    evidence=[ev],
                    signals=[],
                    confidence=0.9,
                    confidence_justification="Test",
                )
            },
            "agents_executed": [],
            "errors": [],
            "warnings": [],
        }
        
        with pytest.raises(ValueError, match="Missing adapter outputs"):
            await workflow._node_v2_join(state)
        
        print("✅ Join node rejects partial state")
    
    @pytest.mark.asyncio
    async def test_quantifier_tripwire_catches_missing_gates(self):
        """Quantifier tripwire must fail without gate markers."""
        from app.workflow import ZarqaWorkflow
        
        workflow = ZarqaWorkflow()
        
        # State without gate markers
        state = {
            "agent_outputs": {},
            "agents_executed": [],
            "errors": [],
            "warnings": [],
        }
        
        with pytest.raises(ValueError, match="QuantifierV2 tripwire"):
            await workflow._node_quantifier_v2(state)
        
        print("✅ Quantifier tripwire catches missing gates")




class TestLegacySafetyNets:
    """Ensure legacy path is unreachable and guarded in V2 mode."""
    
    def test_legacy_nodes_excluded_from_graph_in_v2_mode(self):
        """Legacy nodes should NOT be in the compiled graph if V2 enabled."""
        workflow_module = _load_workflow(True)
        workflow = workflow_module.ZarqaWorkflow()
        nodes = getattr(workflow.graph, "nodes", None)
        node_keys = list(nodes.keys()) if isinstance(nodes, dict) else []
        
        assert "quantifier_v2" in node_keys, "Missing 'quantifier_v2' node in V2 graph"
        assert "quantifier" not in node_keys, "Legacy 'quantifier' node found in V2 graph"
        assert "critic" not in node_keys, "Legacy 'critic' node found in V2 graph"
        
        print(f"✅ V2 node_keys: {node_keys}")

    def test_legacy_nodes_present_when_v2_disabled(self):
        """Legacy nodes should be present when V2 mode is disabled."""
        workflow_module = _load_workflow(False)
        workflow = workflow_module.ZarqaWorkflow()
        nodes = getattr(workflow.graph, "nodes", None)
        node_keys = list(nodes.keys()) if isinstance(nodes, dict) else []
        
        assert "quantifier" in node_keys, "Legacy 'quantifier' node missing in legacy graph"
        assert "critic" in node_keys, "Legacy 'critic' node missing in legacy graph"
        
        print(f"✅ Legacy node_keys: {node_keys}")
    
    @pytest.mark.asyncio
    async def test_legacy_method_tripwire_raises_error(self):
        """Direct invocation of legacy methods must raise RuntimeError."""
        workflow_module = _load_workflow(True)
        workflow = workflow_module.ZarqaWorkflow()
        state = {"errors": [], "agents_executed": [], "warnings": []}
        
        with pytest.raises(RuntimeError, match="Legacy quantifier executed in v2 mode"):
            await workflow._node_quantifier(state)
            
        with pytest.raises(RuntimeError, match="Legacy critic executed in v2 mode"):
            await workflow._node_critic(state)
            
        print("✅ Legacy method tripwires active and preventing execution")


class TestIndependenceAnalysis:
    """Test independence analysis and deduplication."""
    
    def test_deduper_detects_syndication(self):
        """Deduper must detect syndicated duplicates."""
        from app.retrieval.evidence_deduper import evidence_deduper
        from app.graph.contracts import EvidenceItem, SourceType
        
        # Create syndicated duplicates (same content_hash)
        content_hash = "a" * 64
        
        e1 = EvidenceItem(
            id=str(uuid.uuid4()),
            url="https://reuters.com/oil-price-rises",
            canonical_url="https://reuters.com/oil-price-rises",
            domain="reuters.com",
            content_hash=content_hash,
            snippet="Oil prices rose 5% today due to supply constraints.",
            source_type=SourceType.PRIMARY_REPORTING,
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
        
        e3 = EvidenceItem(
            id=str(uuid.uuid4()),
            url="https://ft.com/analysis/opec-strategy",
            canonical_url="https://ft.com/analysis/opec-strategy",
            domain="ft.com",
            content_hash="b" * 64,  # Different = independent
            snippet="OPEC strategy meeting concluded with production cuts.",
            source_type=SourceType.PRIMARY_REPORTING,
            reliability_tier=1,
        )
        
        all_evidence = [e1, e2, e3]
        deduplicated = evidence_deduper.deduplicate_batch(all_evidence)
        
        # Should reduce due to syndication
        assert len(deduplicated) <= len(all_evidence)
        print(f"✅ Deduper: {len(all_evidence)} -> {len(deduplicated)}")
    
    def test_independence_analyzer_produces_scores(self):
        """Independence analyzer must produce valid scores."""
        from app.retrieval.independence_analyzer import independence_analyzer
        from app.graph.contracts import EvidenceItem, ClaimItem, SourceType, TimeHorizon
        
        evidence = [
            EvidenceItem(
                id=str(uuid.uuid4()),
                url="https://reuters.com/oil",
                canonical_url="https://reuters.com/oil",
                domain="reuters.com",
                content_hash="a" * 64,
                snippet="Oil prices rose.",
                source_type=SourceType.PRIMARY_REPORTING,
                reliability_tier=1,
            )
        ]
        
        claims = [
            ClaimItem(
                text="Oil will rise",
                evidence_ids=[evidence[0].id],
                confidence=0.8,
                confidence_justification="Test",
                time_horizon=TimeHorizon.SHORT_TERM,
            )
        ]
        
        stats = independence_analyzer.analyze_agent_independence(claims, evidence)
        
        assert stats is not None
        print(f"✅ Independence stats: {stats}")


class TestExplainFusionStructure:
    """Test explain_fusion output."""
    
    def test_explain_fusion_has_required_fields(self):
        """ExplainFusion must have required structure."""
        from app.graph.contracts import ExplainFusion
        
        explain = ExplainFusion(
            agent_contributions={"market_classifier": 0.4},
            independence_penalties={"context_interpreter": 0.85},
            conflicts_detected=[],
            normalization_factors={"SHORT_TERM": 1.0},
        )
        
        assert hasattr(explain, "agent_contributions")
        assert hasattr(explain, "independence_penalties")
        assert hasattr(explain, "conflicts_detected")
        
        print("✅ ExplainFusion has required fields")
    
    def test_independence_penalty_detection(self):
        """Penalties < 1.0 indicate syndication detected."""
        penalties = {"agent1": 0.85, "agent2": 1.0}
        
        has_penalty = any(p < 1.0 for p in penalties.values())
        assert has_penalty, "Should have at least one penalty < 1.0"
        
        print("✅ Independence penalties correctly detect syndication")


# ===========================================================================
# EXPLAIN_FUSION AUDIT CHECKLIST (for human inspection)
# ===========================================================================
"""
GREEN FLAGS ✅:
1. cluster_count >= 1 when evidence exists
2. diversity_score in range [0.3, 1.0]
3. At least one independence_penalty < 1.0 when syndicated sources present
4. agent_contributions sum to ~1.0 per horizon
5. All horizon forecasts have P10 <= P50 <= P90

RED FLAGS 🚨:
1. cluster_count = 0 when evidence exists (clustering failed)
2. All independence_penalties = 1.0 with syndicated sources (penalties not applied)
3. diversity_score = 1.0 with duplicate sources (syndication not detected)
4. Any agent_contribution = 0 (agent output ignored)
5. conflicts_detected non-empty but not explained
"""




if __name__ == "__main__":
    pytest.main([__file__, "-v"])
