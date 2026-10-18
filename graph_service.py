"""FalkorDB persistence and graph queries for LaunchLens."""
from __future__ import annotations

import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
from falkordb import FalkorDB

load_dotenv()

PROJECT_ID = "launchlens-demo"
GRAPH_NAME = os.getenv("FALKORDB_GRAPH", "launchlens")

SAMPLE_TASKS = [
    {
        "id": "T1", "title": "Agree on the authentication contract",
        "description": "Document token format, expiry, error semantics, and client expectations.",
        "status": "done", "priority": "high", "owner": "API team", "due_date": "2026-10-20",
    },
    {
        "id": "T2", "title": "Implement authentication service",
        "description": "Ship token validation, refresh behavior, and consistent auth errors.",
        "status": "in_progress", "priority": "critical", "owner": "Backend team", "due_date": "2026-10-20",
    },
    {
        "id": "T3", "title": "Integrate sign-in UI",
        "description": "Connect the login screen to the authentication endpoint and handle failures.",
        "status": "todo", "priority": "high", "owner": "Frontend team", "due_date": "2026-10-21",
    },
    {
        "id": "T4", "title": "Run end-to-end integration tests",
        "description": "Verify sign-in, token refresh, expired sessions, and error states in the test environment.",
        "status": "todo", "priority": "critical", "owner": "QA team", "due_date": "2026-10-22",
    },
    {
        "id": "T5", "title": "Provision the test environment",
        "description": "Provide a stable staging environment and test credentials for the release candidate.",
        "status": "done", "priority": "medium", "owner": "Platform team", "due_date": "2026-10-19",
    },
    {
        "id": "T6", "title": "Approve the release candidate",
        "description": "Release only after integration tests and the security review are complete.",
        "status": "todo", "priority": "critical", "owner": "Release owner", "due_date": "2026-10-23",
    },
    {
        "id": "T7", "title": "Complete the authentication security review",
        "description": "Review token lifetime, refresh-token handling, and failure-mode behavior.",
        "status": "todo", "priority": "critical", "owner": "Security team", "due_date": "2026-10-22",
    },
]

# (dependent task, prerequisite task). Direction is important: T3 depends on T2.
SAMPLE_DEPENDENCIES = [
    ("T2", "T1"),
    ("T3", "T2"),
    ("T4", "T3"),
    ("T4", "T5"),
    ("T6", "T4"),
    ("T6", "T7"),
    ("T7", "T2"),
    ("T7", "T5"),
]

SAMPLE_DECISIONS = [
    {
        "id": "D1", "title": "Access tokens must be short-lived",
        "details": "Use short-lived access tokens and rotate refresh tokens; review the implementation and edge cases before release.",
        "affected_tasks": ["T1", "T2", "T3", "T7"],
    },
    {
        "id": "D2", "title": "Release requires both integration tests and security review",
        "details": "The release candidate must not be approved until the end-to-end suite and authentication security review are complete.",
        "affected_tasks": ["T4", "T6", "T7"],
    },
]


class GraphService:
    def __init__(self) -> None:
        self.host = os.getenv("FALKORDB_HOST", "localhost")
        self.port = int(os.getenv("FALKORDB_PORT", "6379"))
        self.username = os.getenv("FALKORDB_USERNAME") or None
        self.password = os.getenv("FALKORDB_PASSWORD") or None
        self.db = FalkorDB(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
        )
        self.graph = self.db.select_graph(GRAPH_NAME)

    def query(self, cypher: str, params: dict[str, Any] | None = None) -> list[list[Any]]:
        """Run a parameterized Cypher query against FalkorDB."""
        return self.graph.query(cypher, params or {}).result_set

    def wait_until_ready(self, timeout_seconds: int = 30) -> None:
        deadline = time.monotonic() + timeout_seconds
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            try:
                rows = self.query("RETURN 1 AS ok")
                if rows and rows[0][0] == 1:
                    return
            except Exception as exc:  # database may still be starting
                last_error = exc
            time.sleep(0.5)
        raise ConnectionError(
            f"Could not connect to FalkorDB at {self.host}:{self.port}. "
            "Start the database with `docker compose up -d falkordb`. "
            f"Last error: {last_error}"
        )

    def ensure_demo_data(self) -> bool:
        """Idempotently create the synthetic release graph and repair missing seed edges.

        Existing task status edits are preserved. Returns True only when the project
        root did not exist before this call (first-time seed for the UI toast).
        """
        existing = self.query("MATCH (p:Project {id: $id}) RETURN p.id", {"id": PROJECT_ID})
        seeded = not bool(existing)
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")

        self.query(
            "MERGE (p:Project {id: $id}) "
            "ON CREATE SET p.name = $name, p.description = $description, p.created_at = $created_at",
            {
                "id": PROJECT_ID,
                "name": "LaunchLens — Authentication Release",
                "description": "Synthetic software-release graph for explaining blockers and downstream impact.",
                "created_at": now,
            },
        )
        for task in SAMPLE_TASKS:
            props = {**task, "updated_at": now}
            self.query(
                "MERGE (t:Task {id: $id}) ON CREATE SET "
                "t.title = $title, t.description = $description, t.status = $status, "
                "t.priority = $priority, t.owner = $owner, t.due_date = $due_date, t.updated_at = $updated_at",
                props,
            )
            self.query(
                "MATCH (p:Project {id: $project_id}), (t:Task {id: $task_id}) "
                "MERGE (p)-[:HAS_TASK]->(t)",
                {"project_id": PROJECT_ID, "task_id": task["id"]},
            )

        for task_id, dependency_id in SAMPLE_DEPENDENCIES:
            self.query(
                "MATCH (t:Task {id: $task_id}), (d:Task {id: $dependency_id}) "
                "MERGE (t)-[:DEPENDS_ON]->(d)",
                {"task_id": task_id, "dependency_id": dependency_id},
            )

        for decision in SAMPLE_DECISIONS:
            self.query(
                "MERGE (d:Decision {id: $id}) ON CREATE SET "
                "d.title = $title, d.details = $details, d.created_at = $created_at",
                {"id": decision["id"], "title": decision["title"], "details": decision["details"], "created_at": now},
            )
            for task_id in decision["affected_tasks"]:
                self.query(
                    "MATCH (d:Decision {id: $decision_id}), (t:Task {id: $task_id}) "
                    "MERGE (d)-[:AFFECTS]->(t)",
                    {"decision_id": decision["id"], "task_id": task_id},
                )
        return seeded

    def get_project(self) -> dict[str, Any]:
        rows = self.query("MATCH (p:Project {id: $id}) RETURN p.id, p.name, p.description", {"id": PROJECT_ID})
        if not rows:
            return {"id": PROJECT_ID, "name": "LaunchLens", "description": "Graph-powered release readiness and dependency impact agent"}
        return {"id": rows[0][0], "name": rows[0][1], "description": rows[0][2]}

    def list_tasks(self) -> list[dict[str, Any]]:
        rows = self.query(
            "MATCH (p:Project {id: $project_id})-[:HAS_TASK]->(t:Task) "
            "RETURN t.id, t.title, t.description, t.status, t.priority, t.owner, t.due_date, t.updated_at "
            "ORDER BY t.id",
            {"project_id": PROJECT_ID},
        )
        tasks = []
        for row in rows:
            task = {
                "id": row[0], "title": row[1], "description": row[2], "status": row[3],
                "priority": row[4], "owner": row[5], "due_date": row[6], "updated_at": row[7],
            }
            task["dependencies"] = self.get_direct_dependencies(task["id"])
            tasks.append(task)
        return tasks

    def get_direct_dependencies(self, task_id: str) -> list[dict[str, Any]]:
        rows = self.query(
            "MATCH (t:Task {id: $task_id})-[:DEPENDS_ON]->(d:Task) "
            "RETURN d.id, d.title, d.status ORDER BY d.id",
            {"task_id": task_id},
        )
        return [{"id": r[0], "title": r[1], "status": r[2]} for r in rows]

    def get_ready_tasks(self) -> list[dict[str, Any]]:
        """Let FalkorDB traverse DEPENDS_ON to find unfinished, unblocked tasks."""
        rows = self.query(
            "MATCH (p:Project {id: $project_id})-[:HAS_TASK]->(t:Task) "
            "WHERE t.status IN ['todo', 'in_progress'] "
            "OPTIONAL MATCH (t)-[:DEPENDS_ON]->(dep:Task) "
            "WITH t, collect(dep) AS deps "
            "WHERE all(dep IN deps WHERE dep.status = 'done') "
            "OPTIONAL MATCH (downstream:Task)-[:DEPENDS_ON*1..]->(t) "
            "WHERE downstream.id <> t.id AND downstream.status IN ['todo', 'in_progress', 'blocked'] "
            "WITH t, deps, count(DISTINCT downstream) AS downstream_count "
            "RETURN t.id, t.title, t.description, t.status, t.priority, t.owner, t.due_date, "
            "size(deps) AS dependency_count, downstream_count",
            {"project_id": PROJECT_ID},
        )
        priority_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        tasks = [
            {"id": r[0], "title": r[1], "description": r[2], "status": r[3], "priority": r[4],
             "owner": r[5], "due_date": r[6], "dependency_count": r[7],
             "downstream_count": int(r[8]) if len(r) > 8 and r[8] is not None else 0}
            for r in rows
        ]
        # Prefer current work, then higher priority; use graph-computed downstream
        # reach as a tie-breaker so a task that unblocks more work rises within its tier.
        tasks.sort(key=lambda t: (
            0 if t["status"] == "in_progress" else 1,
            priority_rank.get(t["priority"], 9),
            -t["downstream_count"],
            t["due_date"] or "",
        ))
        return tasks

    def get_blocked_tasks(self) -> list[dict[str, Any]]:
        """Find unfinished tasks with any unfinished prerequisite on a graph path."""
        rows = self.query(
            "MATCH (p:Project {id: $project_id})-[:HAS_TASK]->(t:Task) "
            "WHERE t.status IN ['todo', 'in_progress', 'blocked'] "
            "MATCH (t)-[:DEPENDS_ON*1..]->(dep:Task) "
            "WHERE dep.status <> 'done' "
            "RETURN t.id, t.title, t.status, collect(DISTINCT dep.title) AS blockers "
            "ORDER BY t.id",
            {"project_id": PROJECT_ID},
        )
        return [{"id": r[0], "title": r[1], "status": r[2], "blockers": list(r[3] or [])} for r in rows]

    def get_blockers_for_task(self, task_id: str) -> list[dict[str, Any]]:
        rows = self.query(
            "MATCH path=(t:Task {id: $task_id})-[:DEPENDS_ON*1..]->(dep:Task) "
            "WHERE dep.status <> 'done' "
            "RETURN dep.id, dep.title, dep.status, min(length(path)) AS distance "
            "ORDER BY distance",
            {"task_id": task_id},
        )
        return [{"id": r[0], "title": r[1], "status": r[2], "distance": r[3]} for r in rows]

    def get_downstream_impact(self, task_id: str) -> list[dict[str, Any]]:
        """Trace unfinished downstream tasks that depend on this task, at any depth.

        The path direction is intentionally reversed from the prerequisite traversal:
        every returned task has a DEPENDS_ON path leading to the selected task.
        This is the project's explainable "what gets unblocked?" analysis.
        """
        rows = self.query(
            "MATCH (target:Task {id: $task_id}), (downstream:Task) "
            "WHERE downstream.status <> 'done' AND downstream.id <> target.id "
            "MATCH path = allShortestPaths((downstream)-[:DEPENDS_ON*1..]->(target)) "
            "WITH downstream, target, length(path) AS distance, "
            "collect(DISTINCT [n IN nodes(path) | n.title]) AS dependency_paths "
            "OPTIONAL MATCH (downstream)-[:DEPENDS_ON]->(direct_dep:Task) "
            "WITH downstream, target, distance, dependency_paths, collect(direct_dep) AS direct_deps "
            "WITH downstream, target, distance, dependency_paths, "
            "(downstream.status IN ['todo', 'in_progress'] AND "
            "all(dep IN direct_deps WHERE dep.status = 'done' OR dep.id = target.id)) AS ready_if_target_done "
            "OPTIONAL MATCH (d:Decision)-[:AFFECTS]->(downstream) "
            "RETURN downstream.id, downstream.title, downstream.status, distance, dependency_paths, "
            "ready_if_target_done, collect(DISTINCT d.title) AS linked_decisions "
            "ORDER BY distance, downstream.id",
            {"task_id": task_id},
        )
        return [
            {
                "id": row[0],
                "title": row[1],
                "status": row[2],
                "distance": row[3],
                "paths": [list(path) for path in (row[4] or [])],
                "ready_if_target_done": bool(row[5]),
                "linked_decisions": list(row[6] or []),
            }
            for row in rows
        ]

    def list_decisions(self) -> list[dict[str, Any]]:
        rows = self.query(
            "MATCH (d:Decision)-[:AFFECTS]->(t:Task) "
            "RETURN d.id, d.title, d.details, d.created_at, collect(DISTINCT t.title) AS affected_tasks "
            "ORDER BY d.created_at DESC",
            {},
        )
        return [{"id": r[0], "title": r[1], "details": r[2], "created_at": r[3], "affected_tasks": list(r[4] or [])} for r in rows]

    def list_relationships(self) -> dict[str, list[dict[str, str]]]:
        dep_rows = self.query(
            "MATCH (t:Task)-[:DEPENDS_ON]->(d:Task) RETURN t.id, t.title, d.id, d.title ORDER BY t.id, d.id"
        )
        affect_rows = self.query(
            "MATCH (d:Decision)-[:AFFECTS]->(t:Task) RETURN d.id, d.title, t.id, t.title ORDER BY d.id, t.id"
        )
        return {
            "dependencies": [{"task_id": r[0], "task": r[1], "dependency_id": r[2], "depends_on": r[3]} for r in dep_rows],
            "decision_links": [{"decision_id": r[0], "decision": r[1], "task_id": r[2], "task": r[3]} for r in affect_rows],
        }

    def update_task_status(self, task_id: str, status: str) -> None:
        allowed = {"todo", "in_progress", "blocked", "done"}
        if status not in allowed:
            raise ValueError(f"Unknown status: {status}")
        if status == "done":
            blockers = self.get_blockers_for_task(task_id)
            if blockers:
                names = ", ".join(item["title"] for item in blockers)
                raise ValueError(f"Cannot mark this task done yet. Finish its prerequisite(s) first: {names}.")
        rows = self.query(
            "MATCH (t:Task {id: $task_id}) SET t.status = $status, t.updated_at = $updated_at RETURN t.id",
            {"task_id": task_id, "status": status, "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")},
        )
        if not rows:
            raise ValueError("Task not found.")

    def add_task(self, title: str, description: str, priority: str, owner: str, due_date: str, dependencies: list[str]) -> str:
        title = title.strip()
        if not title:
            raise ValueError("Task title is required.")
        if priority not in {"critical", "high", "medium", "low"}:
            raise ValueError("Priority must be critical, high, medium, or low.")

        dependency_ids = list(dict.fromkeys(dependencies))
        if dependency_ids:
            existing_rows = self.query(
                "MATCH (t:Task) WHERE t.id IN $task_ids RETURN t.id",
                {"task_ids": dependency_ids},
            )
            existing_ids = {row[0] for row in existing_rows}
            missing_ids = sorted(set(dependency_ids) - existing_ids)
            if missing_ids:
                raise ValueError("Unknown prerequisite task ID(s): " + ", ".join(missing_ids))

        task_id = "T-" + uuid.uuid4().hex[:7].upper()
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        created = self.query(
            "MATCH (p:Project {id: $project_id}) "
            "CREATE (t:Task {id: $id, title: $title, description: $description, status: 'todo', "
            "priority: $priority, owner: $owner, due_date: $due_date, updated_at: $updated_at}) "
            "CREATE (p)-[:HAS_TASK]->(t) RETURN t.id",
            {"project_id": PROJECT_ID, "id": task_id, "title": title, "description": description,
             "priority": priority, "owner": owner.strip() or "Unassigned", "due_date": due_date, "updated_at": now},
        )
        if not created:
            raise ValueError("Could not create the task. Confirm that the project node exists in FalkorDB.")
        for dependency_id in dependency_ids:
            self.query(
                "MATCH (t:Task {id: $task_id}), (d:Task {id: $dependency_id}) "
                "CREATE (t)-[:DEPENDS_ON]->(d)",
                {"task_id": task_id, "dependency_id": dependency_id},
            )
        return task_id

    def add_decision(self, title: str, details: str, affected_task_ids: list[str]) -> str:
        if not title.strip() or not details.strip():
            raise ValueError("Decision title and details are required.")
        if not affected_task_ids:
            raise ValueError("Link the decision to at least one task to preserve graph context.")

        task_ids = list(dict.fromkeys(affected_task_ids))
        existing_rows = self.query(
            "MATCH (t:Task) WHERE t.id IN $task_ids RETURN t.id",
            {"task_ids": task_ids},
        )
        existing_ids = {row[0] for row in existing_rows}
        missing_ids = sorted(set(task_ids) - existing_ids)
        if missing_ids:
            raise ValueError("Cannot link decision; unknown task ID(s): " + ", ".join(missing_ids))

        decision_id = "D-" + uuid.uuid4().hex[:7].upper()
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        created = self.query(
            "CREATE (d:Decision {id: $id, title: $title, details: $details, created_at: $created_at}) RETURN d.id",
            {"id": decision_id, "title": title.strip(), "details": details.strip(), "created_at": now},
        )
        if not created:
            raise ValueError("Could not create the decision node in FalkorDB.")
        for task_id in task_ids:
            rows = self.query(
                "MATCH (d:Decision {id: $decision_id}), (t:Task {id: $task_id}) "
                "CREATE (d)-[:AFFECTS]->(t) RETURN t.id",
                {"decision_id": decision_id, "task_id": task_id},
            )
            if not rows:
                raise ValueError(f"Could not link decision to task {task_id}.")
        return decision_id

    def counts(self) -> dict[str, int]:
        task_rows = self.query("MATCH (t:Task) RETURN count(t)")
        decision_rows = self.query("MATCH (d:Decision) RETURN count(d)")
        dependency_rows = self.query("MATCH ()-[r:DEPENDS_ON]->() RETURN count(r)")
        affect_rows = self.query("MATCH ()-[r:AFFECTS]->() RETURN count(r)")
        return {
            "tasks": int(task_rows[0][0]) if task_rows else 0,
            "decisions": int(decision_rows[0][0]) if decision_rows else 0,
            "dependencies": int(dependency_rows[0][0]) if dependency_rows else 0,
            "decision_links": int(affect_rows[0][0]) if affect_rows else 0,
        }

    def reset_demo_graph(self) -> None:
        self.query("MATCH (n) DETACH DELETE n")
        self.ensure_demo_data()
