# LaunchLens — Graph-Powered Release Readiness

**See the blast radius before you ship.**

LaunchLens is a release-readiness assistant designed for the **Agents That Act on Connected Data** track at Graph Hacks 2026. It uses **FalkorDB as its primary graph database** to reason over software tasks, prerequisites, downstream impact, decisions, and release gates.

> **Repository status:** This repository currently contains the project overview only. The runnable source bundle has not yet been uploaded here, so do not submit this repository as a complete source-code submission until the project files are present.

## What it does

- Finds unfinished prerequisites and release blockers.
- Explains downstream impact and dependency paths.
- Connects decisions to affected work so teams can recover the reasoning behind a release.
- Flags contradictory task states when prerequisites remain incomplete.
- Uses synthetic demo data; no private company data is required.

## Project bundle

The project archive prepared for this submission is named `launchlens-graph-hacks.zip`. It contains the Streamlit application, FalkorDB graph service, agent logic, tests, Docker configuration, Cypher examples, and setup/submission guides.

**Next step:** upload and extract the contents of that archive into this repository, preserving the `tests/` and `scripts/` folders. The root should contain files such as `app.py`, `graph_service.py`, `agent.py`, `docker-compose.yml`, `requirements.txt`, `queries.cypher`, and the full README.

## Intended quick start

1. Install Docker Desktop and Python 3.11+.
2. Copy `.env.example` to `.env`.
3. Run `docker compose up --build`.
4. Open the app at [http://localhost:8501](http://localhost:8501). FalkorDB Browser is at [http://localhost:3000](http://localhost:3000).
5. Run unit tests with `py -m pytest -q`.
6. Run the included live smoke test against a disposable demo graph before claiming end-to-end validation.

## Graph approach

The intended graph model represents projects, tasks, decisions, prerequisite relationships, project membership, and decision-to-task links. Cypher traversals identify blockers and downstream effects; graph paths provide explainable evidence for readiness decisions. The detailed graph model and query examples are in the prepared project archive.

## Validation status

The prepared project bundle's test report records **19 unit tests passed** and Python compilation checks passed in the packaging environment. A full Docker + live FalkorDB end-to-end run was not available in that environment; it still needs to be verified on the demo machine.

## AI assistance disclosure

AI assistance was used to help develop and document this project. The participant should review, run, understand, and be able to explain the code and architecture before submission. Include the project's AI disclosure file when uploading the full source.

## License

The prepared source bundle includes an MIT license. Include it in this repository with the source files.