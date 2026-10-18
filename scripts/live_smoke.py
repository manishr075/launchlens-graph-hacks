"""Live FalkorDB smoke test for LaunchLens's graph-dependent workflows.

Run with `python scripts/live_smoke.py --reset` against a disposable LaunchLens graph.
The reset flag deletes all nodes in the configured graph before reseeding sample data.
"""
from __future__ import annotations

import argparse
import sys

from graph_service import GraphService


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete and recreate all data in the configured graph (use only for the demo graph).",
    )
    args = parser.parse_args()

    service = GraphService()
    service.wait_until_ready(timeout_seconds=30)

    if args.reset:
        print("Resetting the configured graph. Ensure it contains only disposable LaunchLens demo data.")
        service.reset_demo_graph()
    else:
        seeded = service.ensure_demo_data()
        if seeded:
            print("Seeded the synthetic LaunchLens demo graph.")

    checks: list[tuple[str, bool, str]] = []

    tasks = {task["id"]: task for task in service.list_tasks()}
    checks.append(("Synthetic task data exists", all(key in tasks for key in ("T2", "T3", "T4", "T6", "T7")), f"found {len(tasks)} tasks"))

    ready_ids = {task["id"] for task in service.get_ready_tasks()}
    checks.append(("Graph readiness query", "T2" in ready_ids, f"ready task IDs: {', '.join(sorted(ready_ids)) or '(none)'}"))

    blocker_ids = {item["id"] for item in service.get_blockers_for_task("T6")}
    checks.append(("Multi-hop blocker traversal", {"T2", "T3", "T4"}.issubset(blocker_ids), f"unfinished upstream IDs for T6: {', '.join(sorted(blocker_ids)) or '(none)'}"))

    impact_rows = service.get_downstream_impact("T2")
    impact_by_id = {item["id"]: item for item in impact_rows}
    impact_ids = set(impact_by_id)
    expected_paths = {"T3", "T4", "T6", "T7"}.issubset(impact_ids)
    readiness_flags = (
        impact_by_id.get("T3", {}).get("ready_if_target_done") is True
        and impact_by_id.get("T7", {}).get("ready_if_target_done") is True
        and impact_by_id.get("T4", {}).get("ready_if_target_done") is False
        and impact_by_id.get("T6", {}).get("ready_if_target_done") is False
    )
    t3_paths = impact_by_id.get("T3", {}).get("paths", [])
    named_path_ok = bool(t3_paths and t3_paths[0] == ["Integrate sign-in UI", "Implement authentication service"])
    checks.append(("Reverse impact + immediate-vs-later distinction + named shortest path", expected_paths and readiness_flags and named_path_ok, f"downstream IDs for T2: {', '.join(sorted(impact_ids)) or '(none)'}; T3/T7 should become ready, T4/T6 remain later; T3 path: {t3_paths[0] if t3_paths else '(missing)'}"))

    decisions = service.list_decisions()
    checks.append(("Persistent decision memory", bool(decisions) and any(d["affected_tasks"] for d in decisions), f"retrieved {len(decisions)} linked decisions"))

    release_blockers = {item["id"] for item in service.get_blockers_for_task("T6")}
    checks.append(("Release gate blocks on prerequisites", {"T2", "T3", "T4", "T7"}.issubset(release_blockers), f"unfinished upstream tasks for T6: {', '.join(sorted(release_blockers)) or '(none)'}"))

    original_status = tasks["T2"]["status"]
    mutation_passed = False
    mutation_detail = ""
    changed = False
    try:
        service.update_task_status("T2", "done")
        changed = True
        post_update_ready = {task["id"] for task in service.get_ready_tasks()}
        mutation_passed = {"T3", "T7"}.issubset(post_update_ready)
        mutation_detail = f"ready after T2=done: {', '.join(sorted(post_update_ready)) or '(none)'}"
    except Exception as exc:
        mutation_detail = f"status update/query failed: {exc}"
    finally:
        if changed:
            try:
                service.update_task_status("T2", original_status)
            except Exception as exc:
                mutation_passed = False
                mutation_detail += f"; WARNING could not restore T2 status: {exc}"
    checks.append(("Persisted task update changes readiness", mutation_passed, mutation_detail))

    for label, passed, detail in checks:
        print(f"{'PASS' if passed else 'FAIL'} | {label} | {detail}")

    failed = [label for label, passed, _ in checks if not passed]
    if failed:
        print("\nSmoke test failed: " + "; ".join(failed), file=sys.stderr)
        print("For a clean disposable graph, rerun with --reset. This clears the configured graph.", file=sys.stderr)
        return 1

    print(f"\nAll {len(checks)} live FalkorDB smoke checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
