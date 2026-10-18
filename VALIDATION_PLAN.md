# LaunchLens — quick user-validation protocol

This is a protocol, not a completed study. Fill in observations only after real participants try the working application.

## Goal

Check whether LaunchLens helps a small software-project teammate reason about a release dependency chain more accurately or quickly than reading a flat list.

## Participants and privacy

Recruit two classmates or teammates who did not build the app. Ask permission to time task completion and take anonymous notes. Do not collect names, contact details, credentials, or private project information. Use only the bundled synthetic authentication-release graph.

## Procedure (about 8–10 minutes per person)

1. Give the participant the synthetic task list and ask: “Is the release ready? Name the unfinished work that blocks approval.” Record elapsed seconds and correctness before showing LaunchLens.
2. Ask: “If T2 is completed, what becomes ready immediately, and what remains later in the chain?” Record elapsed seconds and correctness from the flat list.
3. Open LaunchLens and ask the same two questions using the app. Record elapsed seconds and correctness, then ask them to retrieve the short-lived-token decision.
4. Ask one rating question: “How easy was it to understand why LaunchLens gave its answer?” (1 = very difficult, 5 = very easy.) Record any confusing UI state or wrong answer.
5. If possible, switch task order for the second participant to reduce simple practice effects. Keep the questions and synthetic data identical.

## Correct-answer key for the bundled graph

- The release is **NOT READY**.
- The incomplete upstream work includes authentication implementation, sign-in UI integration, end-to-end integration tests, and security review.
- If T2 is done, T3 and T7 can become ready immediately; T4 and T6 remain later because other prerequisites are incomplete.
- The decision “Access tokens must be short-lived” should be retrievable through the connected decision graph.

## Record results honestly

| Participant | Flat-list blocker task: seconds / correct? | LaunchLens blocker task: seconds / correct? | Flat-list impact task: seconds / correct? | LaunchLens impact task: seconds / correct? | Ease rating 1–5 | Notes |
|---|---|---|---|---|---:|---|
| P1 | Not tested | Not tested | Not tested | Not tested | — | Fill after test |
| P2 | Not tested | Not tested | Not tested | Not tested | — | Fill after test |

Do not infer a reliable population-level benefit from two people. With n=2, report individual results and qualitative feedback, not a generalized time-saving claim. If you cannot run this test before submission, state that user validation remains future work.
