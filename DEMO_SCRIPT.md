# LaunchLens demo script (2 min 45 sec)

**Track:** Agents That Act on Connected Data  
**Record only after the live FalkorDB smoke test passes.** This is a script, not proof that the run has been recorded or verified.

## 0:00–0:15 — The problem

“Release checklists show open tickets, but they hide the chain of prerequisites and the decisions behind them. LaunchLens uses a graph to explain whether a release is ready and what a change will affect.”

## 0:15–0:35 — Start with a release decision

On the actual app home screen, show the release gate and ask: **“Can we release?”** The answer should say **NOT READY** and list unfinished tasks on paths to the release candidate. Point to FalkorDB in the connection status.

## 0:35–1:10 — Demonstrate multi-hop blast radius

Ask: **“What gets unblocked if T2 is done?”** Show that:

- T3, *Integrate sign-in UI*, would be ready immediately.
- T7, *Complete the authentication security review*, would also be ready immediately because its other prerequisite is done.
- T4, *Run end-to-end integration tests*, remains later because it depends on T3.
- T6, *Approve the release candidate*, remains later because it needs both integration tests and the security review.

Open the live relationship map, then expand exact graph evidence and point out the named shortest path printed for T3: `Integrate sign-in UI → Implement authentication service`. Show the reversed `DEPENDS_ON` traversal. Explain why a simple list or keyword search would not calculate this dependency chain by itself.

## 1:10–1:35 — Prove the graph is load-bearing

Open **Graph evidence** and show dependency and decision edges. Explain the schema: `Task-[:DEPENDS_ON]->Task` means the first task requires the second; `Decision-[:AFFECTS]->Task` links a policy to relevant work. The query result, not a hard-coded paragraph, determines the recommendation.

## 1:35–2:05 — Change state and rerun

In the Task board, mark T2 as `done`. Ask the next-action question again. T3 and T7 should now be eligible. Ask **“Can we release?”** again: the release should still be blocked by the remaining downstream checks. This is the central proof that state changes in FalkorDB affect future recommendations.

## 2:05–2:25 — Show decision recall

Ask **“What decision should I remember about authentication?”** or use the decision-memory tab. Show the short-lived-token policy linked to authentication implementation and security review.

## 2:25–2:45 — Close with honest scope

“LaunchLens makes release dependency paths and linked decisions inspectable in FalkorDB. It is a local hackathon prototype using synthetic data. It helps teams reason about release readiness; it does not deploy code or certify production safety.”

## Recording checklist

- Start recording with the app already loaded and the database connected.
- Use the synthetic sample graph and reset before recording if prior interactions changed it.
- Verify the smoke-test result before the video; do not fake a database status or paste made-up terminal output.
- Ensure text is readable at the chosen screen resolution and the video link opens in an incognito window.
