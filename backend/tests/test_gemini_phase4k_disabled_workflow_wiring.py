from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = ROOT / "backend" / "app" / "workflow.py"


def _workflow_source() -> str:
    return WORKFLOW_PATH.read_text(encoding="utf-8")


def _workflow_tree() -> ast.Module:
    return ast.parse(_workflow_source())


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _string_literals(node: ast.AST) -> list[str]:
    values: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            values.append(child.value)
    return values


def _literal_or_name(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return ast.unparse(node)


def test_workflow_imports_only_noop_graph_adapter_symbol():
    tree = _workflow_tree()
    graph_adapter_imports = [
        node
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module == "app.integrations.gemini_deep_research.graph_adapter"
    ]

    assert len(graph_adapter_imports) == 1
    assert [alias.name for alias in graph_adapter_imports[0].names] == [
        "gemini_graph_noop_node"
    ]


def test_workflow_does_not_import_live_gemini_execution_paths():
    source = _workflow_source()

    assert "GeminiDeepResearchClient" not in source
    assert "GeminiAssistNodeWrapper" not in source
    assert "live_review_runner" not in source
    assert "GEMINI_API_KEY" not in source


def test_workflow_registers_disabled_noop_node_only():
    tree = _workflow_tree()
    add_node_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and _call_name(node.func) == "add_node"
        and _string_literals(node)
    ]
    gemini_add_node_calls = [
        node for node in add_node_calls if "gemini_assist_noop" in _string_literals(node)
    ]

    assert len(gemini_add_node_calls) == 1
    call = gemini_add_node_calls[0]
    assert isinstance(call.args[0], ast.Constant)
    assert call.args[0].value == "gemini_assist_noop"
    assert isinstance(call.args[1], ast.Name)
    assert call.args[1].id == "gemini_graph_noop_node"


def test_v2_join_proceed_routes_only_to_noop_then_schema_validator():
    tree = _workflow_tree()
    add_conditional_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and _call_name(node.func) == "add_conditional_edges"
        and "v2_join_node" in _string_literals(node)
    ]

    assert len(add_conditional_calls) == 1
    call = add_conditional_calls[0]
    route_map = next(arg for arg in call.args if isinstance(arg, ast.Dict))
    routes = {
        key.value: _literal_or_name(value)
        for key, value in zip(route_map.keys, route_map.values)
        if isinstance(key, ast.Constant)
    }

    assert routes["proceed"] == "gemini_assist_noop"
    assert routes["wait"] == "END"

    add_edge_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and _call_name(node.func) == "add_edge"
    ]
    literal_edges = [
        tuple(_string_literals(node)[:2])
        for node in add_edge_calls
        if len(_string_literals(node)) >= 2
    ]

    assert ("gemini_assist_noop", "schema_validator_node") in literal_edges
    assert ("gemini_assist_noop", "evidence_analyst") not in literal_edges


def test_workflow_does_not_introduce_evidence_analyst_route():
    source = _workflow_source()

    assert "evidence_analyst" not in source


def test_workflow_does_not_add_gemini_state_or_barrier_bookkeeping():
    source = _workflow_source()

    assert 'agent_outputs["gemini' not in source
    assert "agent_outputs['gemini" not in source
    assert 'agent_outputs["gemini_assist_noop"]' not in source
    assert "agent_outputs['gemini_assist_noop']" not in source
    for line in source.splitlines():
        if any(factory in line for factory in ("Signal(", "HorizonForecast(", "FusionResult(")):
            assert "gemini" not in line.lower()
    assert "active_agents" not in source or "gemini_assist_noop" not in source
    assert "skipped_agents" not in source or "gemini_assist_noop" not in source

    for barrier_key in ("v2_join_ready", "v2_join_complete"):
        assert barrier_key in source

    assert "gemini_assist_noop_done" not in source
    assert "gemini_graph_noop_node_done" not in source
