# Publish the public repository

A real public GitHub repository is required by the hackathon. The local project files are prepared; the public URL does not exist until you publish them under your account.

1. Create a **public** empty repository on GitHub named `launchlens-graph-hacks`. Do not initialize it with a README, license, or `.gitignore` because those files are already in this folder.
2. From this folder, run:

```bash
git init
git add .
git commit -m "Build LaunchLens explainable graph planning agent"
git branch -M main
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/launchlens-graph-hacks.git
git push -u origin main
```

3. Replace `YOUR_GITHUB_USERNAME` with your actual account username. If Git complains that a repository already exists locally or a remote is already set, inspect `git status` / `git remote -v` before retrying.
4. Open the public repository in a private/incognito window to verify access and check that `.env` and API keys are not committed. `.gitignore` excludes `.env`.
5. Follow `DEMO_SCRIPT.md`, record the actual app, upload the video to YouTube as **Public** or **Unlisted**, and verify the link works without requiring sign-in.
6. Copy final URLs into `SUBMISSION_FIELDS.md` and the hackathon form.

## Before you submit

The hackathon rules allow coding assistants but require meaningful participant contribution and the ability to explain the implementation. Run the project, debug it, test against a real FalkorDB instance, personalize it with a useful original improvement, and be ready to explain the Cypher queries. The included unit tests cover only the deterministic answer-routing layer; they do not replace an integration test against FalkorDB.
