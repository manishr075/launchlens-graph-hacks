# LaunchLens — Windows Setup, Verification, and Submission Guide

This guide assumes Windows 11 and a solo submission. Follow the phases in order. Do not record or submit unverified links.

## Phase 1 — Extract the project

1. Download `launchlens-graph-hacks.zip` from the chat.
2. In File Explorer, right-click it and choose **Extract All**.
3. Open the extracted `launchlens-graph-hacks` folder. You should see `app.py`, `graph_service.py`, `agent.py`, `docker-compose.yml`, `requirements.txt`, and `README.md`.
4. Open PowerShell in that directory: click the address bar, type `powershell`, then press Enter.

## Phase 2 — Check prerequisites

Install Docker Desktop for Windows and launch it. Wait until Docker Desktop says its engine is running. Install Python 3.10+ if needed.

Run:

```powershell
py --version
docker --version
docker compose version
```

If Docker says it cannot connect to the engine, start Docker Desktop before continuing.

## Phase 3 — Start the product

In PowerShell, inside the project folder:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

The first build downloads the required public container image and Python packages. Keep this terminal open while using the app.

Open these addresses in your browser:

- **LaunchLens:** http://localhost:8501
- **FalkorDB Browser:** http://localhost:3000

The sidebar should say that FalkorDB is connected. The home screen should show the release gate as **NOT READY**. If the connection fails, read the full error shown in the app; check Docker is running and port 6379 is not occupied. Do not continue to the demo while disconnected.

## Phase 4 — Test the core user workflow

Use the synthetic authentication-release example:

1. Ask **Can we release?** Expected: `NOT READY`, with incomplete upstream prerequisites from the graph.
2. Ask **What gets unblocked if T2 is done?** Expected: T3 (*Integrate sign-in UI*) and T7 (*Complete the authentication security review*) can be ready immediately if T2 is completed; T4 and T6 remain later because they have other unfinished prerequisites.
3. Ask **What is blocked and why?** Expected: the app lists tasks with unfinished prerequisite paths.
4. Open **Graph evidence** and inspect the live relationship diagram plus the raw `DEPENDS_ON` and `AFFECTS` links.
5. Open **Task board** and try to mark T6 (*Approve the release candidate*) done. The app should reject it while its upstream prerequisites remain unfinished.
6. Change T2 to `done`. It should persist to FalkorDB. Return to Ask LaunchLens and ask what gets unblocked. T3 and T7 should no longer be blocked by T2, while release approval should remain blocked by integration tests and security review.
7. Open **Decision memory** and inspect the short-lived-token and release-gate decisions. Add a test decision linked to T2, ask about the decision, and confirm it appears.
8. Refresh the browser and confirm the saved task update and decision remain in FalkorDB.

Reset sample data before a pristine test or recording: use the app's **Reset local demo graph** control and confirm it. It deletes all nodes in the configured graph, so only use it with LaunchLens's disposable demo graph.

## Phase 5 — Run automated tests and live checks

Open a **second** PowerShell terminal in the project directory.

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py -m pytest -q
```

Expected unit-test result for the package prepared in this chat: **19 passed**. If the test count differs, examine the error rather than assuming it passed.

With Docker/FalkorDB running and dependencies installed, run the live smoke checks:

```powershell
py scripts/live_smoke.py --reset
```

`--reset` clears and reseeds the graph selected by `FALKORDB_GRAPH`. Use only with the disposable LaunchLens graph. The script must print seven `PASS` lines and finish with “All 7 live FalkorDB smoke checks passed.” If any check fails, fix the query or service implementation and rerun it. The live smoke test was not executed in the packaging environment, so this is a required local action.

## Phase 6 — Understand the core graph model

- `(Project)-[:HAS_TASK]->(Task)` groups tasks into one project.
- `(Task)-[:DEPENDS_ON]->(Task)` means the source task requires the target task to finish first. T3 depends on T2, so the graph query traces from T3 to T2 when looking for blockers.
- `(Decision)-[:AFFECTS]->(Task)` makes a decision retrievable in the context of the tasks it affects.

The next-action query returns active tasks for which all direct prerequisites are done. The blocker query follows `DEPENDS_ON*1..` upstream. The impact query reverses the relationship direction: it starts at a downstream task and follows prerequisite edges until it reaches the task being considered. It checks the downstream task's other direct prerequisites before saying it would become ready immediately.

Try explaining these details in your own words. Submission rules say the participant must understand their code and graph decisions.

## Phase 7 — Create a public GitHub repository

1. Sign in to GitHub in your browser.
2. Click **New repository** and name it `launchlens-graph-hacks`.
3. Set it to **Public**. Do not initialize another README, `.gitignore`, or license because the project already includes them.
4. Copy the repository URL, then run the commands in `PUBLISH.md` from PowerShell within this folder.
5. Check `git status` before committing. Make sure `.env` does not appear; the project `.gitignore` excludes it.
6. Open the repo URL in an incognito window and confirm it is public and files are visible.
7. Ensure the README explains setup, graph schema, main Cypher queries, testing, limitations, and AI disclosure.

Use meaningful commit messages that accurately describe your work. Do not claim tests passed in commit messages until you have run them.

## Phase 8 — Record a real demo

Follow `DEMO_SCRIPT.md`; aim for 2:30–2:50. Record the actual browser showing LaunchLens, not just slides or a static screenshot. Before recording, reset the graph and verify the smoke test passes.

Show these moments early:

- release gate says not ready and names graph-derived upstream blockers;
- T2 downstream impact separates immediately-ready tasks from later tasks;
- the graph tab shows real relationships;
- changing T2 changes future results because the graph state changed;
- a decision can be retrieved through `AFFECTS` links.

Upload to YouTube as **Public** or **Unlisted**, not Private. Open the link in an incognito browser to confirm it plays. The video is not prepared by this package; you must record and upload it yourself.

## Phase 9 — Fill the hackathon form

Copy the project text from `SUBMISSION_FIELDS.md` and use these checks:

- **Project title:** LaunchLens — Graph-Powered Release Readiness
- **Track:** Agents That Act on Connected Data
- **Repository:** actual public GitHub URL
- **Demo video:** actual public/unlisted YouTube URL
- **Live demo or deployment:** actual deployed link if available; otherwise explain that Docker Compose local setup instructions are in README
- **FalkorDB usage:** explain that graph traversals drive readiness, blockers, downstream impact, and decision memory
- **Blog:** leave blank if you didn't publish one
- **Feedback questions:** use the honest drafted answers from `SUBMISSION_FIELDS.md`

Do not paste `YOUR_GITHUB_USERNAME` or `REPLACE_WITH_REAL_VIDEO_ID`; those are placeholders.

## Phase 10 — Final pre-submit verification

- [ ] App opens at `http://localhost:8501` with FalkorDB connected.
- [ ] “Can we release?” reports the expected release gate state.
- [ ] Downstream-impact response distinguishes T3/T7 from T4/T6.
- [ ] Updating T2 changes subsequent answers.
- [ ] Decision memory survives refresh.
- [ ] `py -m pytest -q` passes.
- [ ] `py scripts/live_smoke.py --reset` reports seven passes.
- [ ] Public repo opens in an incognito browser.
- [ ] No `.env`, API key, private data, or credential is committed.
- [ ] Demo video opens to judges without sign-in.
- [ ] The submitted description does not claim production readiness, user validation, measured impact, or live deployment that you did not actually demonstrate.
- [ ] AI coding assistance is disclosed in the repo.
- [ ] Submission is filed before the deadline shown on the official page.

## Remaining honest limitations

This is an explainable prototype over synthetic tasks. It does not connect to a real ticket tracker or deploy code. It has not been validated with external users and has no measured time-saving or production-safety claim. The packaged source was compiled and the unit tests passed, but the full live database and browser workflow must be verified on your computer before submission.
