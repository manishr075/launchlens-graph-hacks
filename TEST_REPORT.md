# LaunchLens test and verification report

Report generated during preparation on October 18, 2026.

## Executed successfully

- `python -m compileall -q app.py agent.py graph_service.py visualization.py scripts tests` — passed.
- `pytest -q` — **19 passed**.
- Generated a representative relationship-map DOT diagram and ran `dot -Tsvg` — passed. This validates DOT syntax, not the running Streamlit UI.

The unit tests use fake services/graphs for deterministic behavior, Cypher query contract assertions, shortest-path query and result mapping, idempotent seed construction, downstream influence scoring, invalid dependency rejection, release-gate semantics (including inconsistent “done” state), task-completion prerequisite checks, and generated graph-map content/escaping. They do not connect to a live database.

## Not executed in this environment

- Docker Compose launch: Docker engine is not installed in the packaging environment.
- `scripts/live_smoke.py --reset`: not executed because there is no live FalkorDB instance.
- Browser UI tests and mobile viewport review: not executed because the Streamlit application was not started against a live graph.
- Live deployment, public GitHub repository, and YouTube demo: not published by this environment.
- User validation and real-world impact measurement: not performed.

## Required before claiming demo readiness

1. Start the project with Docker Compose on a machine with Docker available.
2. Verify that the release gate reports `NOT READY` in the initial sample graph.
3. Run `py -m pytest -q` and confirm 19 passing tests.
4. Run `py scripts/live_smoke.py --reset` and require **7/7 live checks**.
5. Manually verify the workflow from `DEMO_SCRIPT.md`, including that T2 updates persist and the release remains blocked by T4/T7.
6. Record a genuine demo and verify the GitHub/YouTube links from an incognito browser.

Do not relabel the checks in the “not executed” section as passed without running them.
