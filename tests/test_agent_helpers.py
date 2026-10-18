"""Small unit tests for deterministic answer routing using a fake graph service."""
from agent import deterministic_answer


class FakeService:
    def list_tasks(self):
        return [
            {"id": "T1", "title": "Agree on auth contract", "description": "Document auth contract", "status": "done", "priority": "high", "owner": "M", "due_date": "2026-10-18", "dependencies": []},
            {"id": "T2", "title": "Implement authentication service", "description": "Implement token validation", "status": "in_progress", "priority": "critical", "owner": "M", "due_date": "2026-10-18", "dependencies": [{"id": "T1", "title": "Agree on auth contract", "status": "done"}]},
            {"id": "T3", "title": "Integrate sign-in UI", "description": "Connect login screen", "status": "todo", "priority": "high", "owner": "Frontend", "due_date": "2026-10-21", "dependencies": [{"id": "T2", "title": "Implement authentication service", "status": "in_progress"}]},
            {"id": "T6", "title": "Approve the release candidate", "description": "Release only after tests and security review.", "status": "todo", "priority": "critical", "owner": "Release", "due_date": "2026-10-23", "dependencies": []},
        ]

    def get_ready_tasks(self):
        return [{"id": "T2", "title": "Implement authentication service", "description": "Implement token validation", "status": "in_progress", "priority": "critical", "owner": "M", "due_date": "2026-10-18", "dependency_count": 1, "downstream_count": 4}]

    def get_blocked_tasks(self):
        return [{"id": "T3", "title": "Integrate sign-in UI", "status": "todo", "blockers": ["Implement authentication service"]}]

    def get_blockers_for_task(self, task_id):
        if task_id == "T3":
            return [{"id": "T2", "title": "Implement authentication service", "status": "in_progress", "distance": 1}]
        if task_id == "T6":
            return [
                {"id": "T2", "title": "Implement authentication service", "status": "in_progress", "distance": 1},
                {"id": "T3", "title": "Integrate sign-in UI", "status": "todo", "distance": 2},
            ]
        return []

    def get_downstream_impact(self, task_id):
        if task_id == "T2":
            return [
                {"id": "T3", "title": "Integrate sign-in UI", "status": "todo", "distance": 1, "paths": [["Integrate sign-in UI", "Implement authentication service"]], "ready_if_target_done": True, "linked_decisions": ["Access tokens must be short-lived"]},
            ]
        return []

    def list_decisions(self):
        return [{"id": "D1", "title": "Access tokens must be short-lived", "details": "Use short-lived access tokens.", "created_at": "2026-10-18", "affected_tasks": ["Implement authentication service", "Integrate sign-in UI"]}]

    def counts(self):
        return {"tasks": 3, "decisions": 1, "dependencies": 2, "decision_links": 2}


def test_next_action_uses_ready_graph_result():
    answer, _ = deterministic_answer("What should I do next?", FakeService())
    assert "Implement authentication service" in answer
    assert "all prerequisite tasks are marked done" in answer
    assert "4 unfinished task(s) depend on this work" in answer


def test_blocker_question_mentions_upstream_task():
    answer, _ = deterministic_answer("Why is Build UI blocked?", FakeService())
    assert "Implement authentication service" in answer
    assert "unfinished prerequisites" in answer


def test_decision_question_retrieves_linked_decision():
    answer, _ = deterministic_answer("What decision should I remember?", FakeService())
    assert "Access tokens must be short-lived" in answer


def test_impact_question_traces_downstream_task_and_related_decision():
    answer, context = deterministic_answer("What gets unblocked if T2 is done?", FakeService())
    assert "Integrate sign-in UI" in answer
    assert "1 relationship hop" in answer
    assert "would be ready immediately" in answer
    assert "Access tokens must be short-lived" in answer
    assert "Shortest dependency path" in answer
    assert "Integrate sign-in UI → Implement authentication service" in answer
    assert context["impact_task"]["id"] == "T2"


def test_release_readiness_is_blocked_by_graph_prerequisites():
    answer, context = deterministic_answer("Can we release?", FakeService())
    assert "NOT READY" in answer
    assert "Implement authentication service" in answer
    assert "release_blockers" in context


def test_blank_question_returns_helpful_message_without_queries():
    answer, context = deterministic_answer("   ", FakeService())
    assert "Ask a concrete question" in answer
    assert context["question"] == "   "


def test_manual_release_block_is_not_reported_as_ready():
    class ManuallyBlockedService(FakeService):
        def list_tasks(self):
            tasks = super().list_tasks()
            for task in tasks:
                if task["id"] == "T6":
                    task["status"] = "blocked"
            return tasks

        def get_blockers_for_task(self, task_id):
            if task_id == "T6":
                return []
            return super().get_blockers_for_task(task_id)

    answer, _ = deterministic_answer("Can we release?", ManuallyBlockedService())
    assert "NOT READY" in answer
    assert "manually marked blocked" in answer


def test_release_status_flag_does_not_overrule_unfinished_graph_prerequisites():
    class InconsistentReleaseService(FakeService):
        def list_tasks(self):
            tasks = super().list_tasks()
            for task in tasks:
                if task["id"] == "T6":
                    task["status"] = "done"
            return tasks

    answer, context = deterministic_answer("Can we release?", InconsistentReleaseService())
    assert "NOT READY" in answer
    assert "inconsistent graph state" in answer
    assert "Implement authentication service" in answer
    assert context["release_blockers"]
