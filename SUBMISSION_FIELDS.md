# Graph Hacks submission form — LaunchLens

**Only paste repository/video links after you have created and opened the real links. Do not submit placeholders.**

## Project title

LaunchLens — Graph-Powered Release Readiness

## Description: What problem does it solve, and who is it for?

Release work is often tracked as a flat checklist, hiding the multi-step dependency chains that make a release unsafe or delayed. LaunchLens is a graph-grounded release-readiness agent for student teams and small software teams. It stores work items, prerequisites, and release decisions in FalkorDB; uses Cypher traversals to trace upstream blockers and downstream blast radius; and explains which tasks would become ready immediately versus later. A release-gate query retrieves unfinished prerequisites before approval, and every result can be inspected as graph evidence. Users can update task state and record decisions; subsequent answers reflect the changed graph. The demo uses synthetic data, and the core flow works without an LLM API key. See `VALIDATION_PLAN.md` for the proposed small user test; do not claim it was completed unless you actually run it.

## Track

**Agents That Act on Connected Data**

## Repository

Replace with the real public repository URL after pushing the source:

`https://github.com/YOUR_GITHUB_USERNAME/launchlens-graph-hacks`

## Demo video

Replace with the real Public or Unlisted YouTube URL after recording the actual working app:

`https://youtu.be/REPLACE_WITH_REAL_VIDEO_ID`

## Live demo or deployment

If a public app is not deployed, the rules accept complete local setup instructions. This repository includes Docker Compose instructions in `README.md`. If a live deployment is created, paste the verified URL here; otherwise state: “Local deployment with Docker Compose; see README Quick start.”

## How did you use FalkorDB?

FalkorDB is the primary database and source of truth for release tasks, dependency relationships, and decision memory. The app uses `Project`, `Task`, and `Decision` nodes with `HAS_TASK`, `DEPENDS_ON`, and `AFFECTS` edges. A parameterized Cypher query finds work whose prerequisites are complete; variable-length traversals find unfinished blockers at any depth; a reverse traversal computes the downstream impact of completing a selected task and distinguishes immediate readiness from later dependencies; and decision retrieval follows `AFFECTS` edges to bring back relevant release policy. The UI writes task-status changes and new task/decision records into FalkorDB, which affects later results. Without FalkorDB, the core readiness, blocker, blast-radius, and decision-recall behavior cannot run.

## Blog link (optional)

Leave blank unless you publish a real blog post.

## Feedback: What did you like about FalkorDB?

Cypher makes dependency questions direct to express: rather than manually joining disconnected task records, the app can trace paths through prerequisites and retrieve decisions connected to affected work. The Python client was straightforward to integrate into the small Streamlit app, and the FalkorDB Browser gives a way to inspect the relationships behind a recommendation.

## Feedback: What improvements would you like to see in FalkorDB?

More complete beginner-oriented examples showing a graph-backed agent that queries, mutates state, handles failed connections, and exposes the evidence behind its answer would help developers move beyond the first query. A compact troubleshooting guide for common Docker/client setup issues and tested examples of more complex variable-length Cypher traversals would also help new builders debug under time pressure.
