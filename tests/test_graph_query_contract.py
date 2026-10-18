"""Unit-level contract checks for graph query construction and result mapping.

These tests do not execute Cypher against a database. Use scripts/live_smoke.py for
live FalkorDB integration verification.
"""
from __future__ import annotations

import sys
import types

import pytest

try:  # Allow source-only unit tests when optional runtime dependencies are absent.
    import falkordb  # noqa: F401
except ImportError:
    fallback = types.ModuleType("falkordb")
    fallback.FalkorDB = object  # type: ignore[attr-defined]
    sys.modules["falkordb"] = fallback

from graph_service import GraphService  # noqa: E402


class FakeResult:
    def __init__(self, rows):
        self.result_set = rows


class FakeGraph:
    def __init__(self, rows):
        self.rows = rows
        self.last_query = ""
        self.last_params = {}
        self.queries = []

    def query(self, query, params=None):
        self.last_query = query
        self.last_params = params or {}
        self.queries.append((query, self.last_params))
        return FakeResult(self.rows)


def test_downstream_impact_uses_reverse_multihop_traversal_and_maps_rows():
    service = GraphService.__new__(GraphService)
    service.graph = FakeGraph([
        ["T3", "Integrate sign-in UI", "todo", 1, [["Integrate sign-in UI", "Implement authentication service"]], True, ["Access tokens must be short-lived"]],
        ["T4", "Run end-to-end tests", "todo", 2, [["Run end-to-end tests", "Integrate sign-in UI", "Implement authentication service"]], False, []],
    ])

    impact = service.get_downstream_impact("T2")

    assert "allShortestPaths((downstream)-[:DEPENDS_ON*1..]->(target))" in service.graph.last_query
    assert "[n IN nodes(path) | n.title]" in service.graph.last_query
    assert "OPTIONAL MATCH (d:Decision)-[:AFFECTS]->(downstream)" in service.graph.last_query
    assert "ready_if_target_done" in service.graph.last_query
    assert service.graph.last_params == {"task_id": "T2"}
    assert impact == [
        {"id": "T3", "title": "Integrate sign-in UI", "status": "todo", "distance": 1, "paths": [["Integrate sign-in UI", "Implement authentication service"]], "ready_if_target_done": True, "linked_decisions": ["Access tokens must be short-lived"]},
        {"id": "T4", "title": "Run end-to-end tests", "status": "todo", "distance": 2, "paths": [["Run end-to-end tests", "Integrate sign-in UI", "Implement authentication service"]], "ready_if_target_done": False, "linked_decisions": []},
    ]


def test_downstream_impact_handles_empty_results():
    service = GraphService.__new__(GraphService)
    service.graph = FakeGraph([])
    assert service.get_downstream_impact("T1") == []


def test_add_task_rejects_unknown_dependency_before_creating_task():
    service = GraphService.__new__(GraphService)
    service.graph = FakeGraph([])
    with pytest.raises(ValueError, match="Unknown prerequisite task ID"):
        service.add_task("Draft README", "Write setup notes", "high", "Manish", "2026-10-18", ["NO-SUCH-TASK"])
    assert not any("CREATE (t:Task" in query for query, _ in service.graph.queries)


def test_add_decision_rejects_unknown_task_before_creating_decision():
    service = GraphService.__new__(GraphService)
    service.graph = FakeGraph([])
    with pytest.raises(ValueError, match="unknown task ID"):
        service.add_decision("API choice", "Use graph storage", ["NO-SUCH-TASK"])
    assert not any("CREATE (d:Decision" in query for query, _ in service.graph.queries)


def test_add_task_rejects_invalid_priority_without_database_access():
    service = GraphService.__new__(GraphService)
    service.graph = FakeGraph([])
    with pytest.raises(ValueError, match="Priority must be"):
        service.add_task("Draft README", "Write setup notes", "urgent-ish", "Manish", "2026-10-18", [])
    assert service.graph.queries == []


def test_seed_uses_merge_for_recoverable_idempotent_demo_graph():
    service = GraphService.__new__(GraphService)
    service.graph = FakeGraph([])
    assert service.ensure_demo_data() is True
    queries = [query for query, _ in service.graph.queries]
    assert any("MERGE (p:Project" in query for query in queries)
    assert any("MERGE (t:Task" in query for query in queries)
    assert any("MERGE (t)-[:DEPENDS_ON]->(d)" in query for query in queries)
    assert any("MERGE (d)-[:AFFECTS]->(t)" in query for query in queries)
    assert not any("CREATE (t:Task" in query for query in queries)


def test_mark_done_is_rejected_when_upstream_prerequisite_is_open():
    service = GraphService.__new__(GraphService)
    service.graph = FakeGraph([])
    service.get_blockers_for_task = lambda task_id: [
        {"id": "T2", "title": "Implement authentication service", "status": "in_progress", "distance": 1}
    ]
    with pytest.raises(ValueError, match="Cannot mark this task done yet"):
        service.update_task_status("T6", "done")
    assert not any("SET t.status" in query for query, _ in service.graph.queries)


def test_ready_query_uses_downstream_graph_reach_for_prioritization():
    service = GraphService.__new__(GraphService)
    service.graph = FakeGraph([
        ["T2", "Implement authentication service", "Ship auth", "in_progress", "critical", "Backend", "2026-10-20", 1, 4],
        ["T5", "Provision test environment", "Stage", "in_progress", "critical", "Platform", "2026-10-20", 0, 2],
    ])
    ready = service.get_ready_tasks()
    assert "[:DEPENDS_ON*1..]" in service.graph.last_query
    assert "count(DISTINCT downstream) AS downstream_count" in service.graph.last_query
    assert ready[0]["id"] == "T2"
    assert ready[0]["downstream_count"] == 4
    assert ready[1]["downstream_count"] == 2


def test_blocked_task_query_includes_manually_blocked_tasks():
    service = GraphService.__new__(GraphService)
    service.graph = FakeGraph([])
    assert service.get_blocked_tasks() == []
    assert "['todo', 'in_progress', 'blocked']" in service.graph.last_query
