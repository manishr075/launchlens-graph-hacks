# LaunchLens — Graph-Powered Release Readiness

**See the blast radius before you ship.**

LaunchLens is a release-readiness assistant that uses **FalkorDB as its primary graph database** to reason over software tasks, prerequisites, downstream impact, decisions, and release gates. It is designed for the **Agents That Act on Connected Data** track at Graph Hacks 2026.

## What it does

- Finds unfinished prerequisites and release blockers.
- Explains downstream impact and dependency paths instead of returning an unsupported yes/no answer.
- Connects decisions to affected work so teams can recover the reasoning behind a release.
- Flags contradictory task states when required prerequisites remain incomplete.
- Uses synthetic demo data; no private company data is required.

## Source bundle

The complete runnable project, including the application, FalkorDB graph service, tests, Docker setup, Cypher examples, and submission guides, is provided in **[LaunchLens source bundle](./LaunchLens-source.zip)**. Download it from this repository and extract it before running.

## Quick start

1. Install Docker Desktop and Python 3.11+.
2. Download and extract `LaunchLens-source.zip`.
3. Open a terminal in the extracted `launchlens-graph-hacks` directory.
4. Copy the environment template: `Copy-Item .env.example .env` (PowerShell) or `cp .env.example .env` (macOS/Linux).
5. Start the app and FalkorDB: `docker compose up --build`.
6. Open the app at [http://localhost:8501](http://localhost:8501). FalkorDB Browser is at [http://localhost:3000](http://localhost:3000).

Run unit tests with `py -m pytest -q`. The source bundle includes a detailed setup/submission guide and a live smoke-test script. The live FalkorDB/Docker flow must be tested on your machine before claiming it has been verified.

## Graph model

- **Nodes:** Project, Task, Decision (and any additional node types documented in the source README).
- **Relationships:** task dependencies, project membership, decision-to-task links, and impact paths.
- **Graph work:** Cypher traversals identify blockers and downstream effects; graph paths provide explainable evidence for readiness decisions.

See `queries.cypher` and the full README inside the source bundle for query details and the complete graph model.

## Validation status

The project bundle's report records **19 unit tests passed** and Python compilation checks passed in the packaging environment. A full Docker + live FalkorDB end-to-end run was not available in that environment; please run the included live smoke test before presenting a successful live demo.

## AI assistance disclosure

AI assistance was used to help develop and document this project. The participant should review, run, understand, and be able to explain the code and architecture before submission. See `AI_DISCLOSURE.md` inside the source bundle.

## Track

**Agents That Act on Connected Data**

## License

See the MIT license included in the source bundle.