"""A graph-grounded planning agent, with optional LLM synthesis."""
from __future__ import annotations

import json
import os
from typing import Any


def _priority_label(priority: str) -> str:
    return priority.replace("_", " ").title()


def deterministic_answer(question: str, service: Any) -> tuple[str, dict[str, Any]]:
    """Answer common project questions from live FalkorDB graph queries."""
    if not question or not question.strip():
        return "Ask a concrete question about release readiness, blockers, downstream impact, or a recorded decision.", {"question": question}

    tasks = service.list_tasks()
    ready = service.get_ready_tasks()
    blocked = service.get_blocked_tasks()
    decisions = service.list_decisions()
    q = question.lower()

    # If the user mentions a known task, scope the answer to that graph node.
    mentioned = next((t for t in tasks if t["title"].lower() in q or t["id"].lower() in q), None)
    context: dict[str, Any] = {"ready_tasks": ready, "blocked_tasks": blocked, "decisions": decisions}

    release_intent = any(
        phrase in q
        for phrase in ("release ready", "ready to release", "can we release", "should we release", "safe to ship", "ready to ship", "release candidate", "release status", "release gate", "release blocker", "release blockers", "release blocked", "release is blocked", "why is release", "why can't we release", "why cant we release", "blocking the release", "blocks the release", "what blocks release", "what is blocking release", "go live", "ship it")
    )
    impact_intent = any(
        phrase in q
        for phrase in ("impact", "unblock", "unlocks", "unlock", "downstream", "blast radius", "who is waiting", "who's waiting", "what gets freed")
    )
    if impact_intent:
        if mentioned:
            impact = service.get_downstream_impact(mentioned["id"])
            context["impact_task"] = mentioned
            context["downstream_impact"] = impact
            if impact:
                lines = [f"**If {mentioned['title']} is completed, these unfinished downstream tasks are affected:**"]
                for item in impact:
                    line = f"- **{item['title']}** (`{item['status']}`; {item.get('distance', '?')} relationship hop(s) downstream)"
                    paths = item.get("paths") or []
                    if paths and paths[0]:
                        line += "\n  - Shortest dependency path: `" + " → ".join(paths[0]) + "`"
                    if item.get("ready_if_target_done"):
                        line += " — **would be ready immediately** if this task is completed."
                    elif item.get("status") == "blocked":
                        line += " — currently marked manually blocked; completing this task alone will not clear that status."
                    else:
                        line += " — affected later in the chain; it still has another unfinished prerequisite."
                    linked = item.get("linked_decisions") or []
                    if linked:
                        line += f"\n  - Related decision memory: {', '.join(linked)}"
                    lines.append(line)
                lines.append("\nThis is a graph-derived impact path. Only direct dependents whose other prerequisites are already done are labeled ready immediately; farther downstream tasks still need their own prerequisites completed.")
                answer = "\n".join(lines)
            else:
                answer = f"No unfinished downstream tasks depend on **{mentioned['title']}** in the current graph. It may be a terminal task or its dependents may already be done."
        else:
            answer = "Name a task ID or exact task title, for example: **What gets unblocked if T2 is done?** I will trace downstream dependency paths and related decisions."
    elif release_intent:
        release_task = next((t for t in tasks if "release candidate" in t["title"].lower() or "release gate" in t["title"].lower()), None)
        if not release_task:
            answer = "I couldn't find a release-gate task in the current graph. Add a release approval task and connect all required checks as prerequisites."
        else:
            blockers_for_release = service.get_blockers_for_task(release_task["id"])
            context["release_gate"] = release_task
            context["release_blockers"] = blockers_for_release
            if release_task["status"] == "done" and blockers_for_release:
                answer = "**Release status: NOT READY — inconsistent graph state.** The release task is marked done, but prerequisite traversal still finds unfinished work:\n" + "\n".join(
                    f"- **{b['title']}** (`{b['status']}`; dependency depth {b.get('distance', '?')})" for b in blockers_for_release
                ) + "\n\nDo not treat the status flag as approval until the dependency chain is resolved."
            elif release_task["status"] == "done":
                answer = f"**Release status: APPROVED** — {release_task['title']} is marked done in FalkorDB and no unfinished prerequisite path was found. This is a workflow state, not a guarantee of production safety."
            elif release_task["status"] == "blocked" and not blockers_for_release:
                answer = f"**Release status: NOT READY** — {release_task['title']} is manually marked blocked, even though no unfinished dependency path was found. Review the task description and resolve that manual blocker before approval."
            elif blockers_for_release:
                answer = "**Release status: NOT READY**\n\nThe graph shows these unfinished prerequisites on paths into the release gate, nearest first:\n" + "\n".join(
                    f"- **{b['title']}** (`{b['status']}`; dependency depth {b.get('distance', '?')})" for b in blockers_for_release
                ) + "\n\nComplete and verify these checks before approving the release candidate."
            else:
                answer = f"**Release status: READY FOR HUMAN APPROVAL** — no unfinished prerequisite path was found for **{release_task['title']}**. This agent does not deploy or approve releases automatically."
    elif any(word in q for word in ("decision", "decided", "remember", "context", "why did we", "why are we")):
        if mentioned:
            decisions = [d for d in decisions if mentioned["title"] in d["affected_tasks"]]
        context["decisions"] = decisions
        if decisions:
            lines = ["**Relevant decisions stored in FalkorDB:**"]
            for d in decisions[:5]:
                lines.append(f"- **{d['title']}** — {d['details']}\n  - Linked tasks: {', '.join(d['affected_tasks'])}")
            answer = "\n".join(lines)
        else:
            answer = "I couldn't find a decision linked to that task in the graph yet. Add a decision and connect it to the affected task so future sessions can retrieve it."
    elif any(word in q for word in ("block", "stuck", "delay", "delayed", "blocked", "why can't", "why cant", "dependency", "depend on")):
        if mentioned:
            blockers_for_task = service.get_blockers_for_task(mentioned["id"])
            context["focused_task"] = mentioned
            context["focused_blockers"] = blockers_for_task
            if blockers_for_task:
                lines = [f"**{mentioned['title']} is waiting on unfinished prerequisites:**"]
                for b in blockers_for_task:
                    lines.append(f"- **{b['title']}** (`{b['status']}`; dependency depth {b.get('distance', '?')})")
                lines.append("\nFinish the closest unfinished prerequisite first. These are graph paths, not keyword guesses.")
                answer = "\n".join(lines)
            else:
                answer = f"No unfinished prerequisite was found on a dependency path for **{mentioned['title']}**. The task may have a manual `blocked` status or a non-dependency issue; inspect its status and description."
        elif blocked:
            lines = ["**Tasks with unfinished prerequisites:**"]
            for task in blocked:
                lines.append(f"- **{task['title']}** — waiting on: {', '.join(task['blockers'])}")
            answer = "\n".join(lines)
        else:
            answer = "There are no unfinished prerequisite paths among the active tasks. Check for tasks manually marked `blocked`."
    elif any(word in q for word in ("next", "priorit", "start", "first", "ready", "what should", "do today", "work on")):
        context["ready_tasks"] = ready
        if ready:
            chosen = ready[0]
            state = "already in progress" if chosen["status"] == "in_progress" else "ready to start"
            answer = (
                f"**Recommended next task: {chosen['title']}** (`{chosen['id']}`)\n\n"
                f"- State: {state}\n- Priority: {_priority_label(chosen['priority'])}\n"
                f"- Owner: {chosen['owner']}\n- Why: all prerequisite tasks are marked done in FalkorDB.\n"
                f"- Downstream impact: {chosen.get('downstream_count', 0)} unfinished task(s) depend on this work, directly or through later steps.\n"
                f"- Suggested action: {chosen['description']}"
            )
            if len(ready) > 1:
                answer += "\n\n**Other graph-ready tasks:** " + "; ".join(t["title"] for t in ready[1:4])
        else:
            answer = "No active task currently satisfies the graph's readiness rule. Inspect unfinished dependency paths and update completed prerequisites."
    else:
        open_tasks = [t for t in tasks if t["status"] != "done"]
        done = sum(1 for t in tasks if t["status"] == "done")
        lines = [f"**Project snapshot:** {done}/{len(tasks)} tasks complete; {len(ready)} ready; {len(blocked)} active tasks blocked by unfinished prerequisites."]
        if ready:
            lines.append(f"**Best next action:** {ready[0]['title']} — {ready[0]['description']}")
        if blocked:
            top = blocked[0]
            lines.append(f"**Dependency risk:** {top['title']} waits on {', '.join(top['blockers'])}.")
        if open_tasks:
            lines.append("**Open tasks:** " + "; ".join(t["title"] for t in open_tasks[:6]))
        answer = "\n\n".join(lines)

    context["question"] = question
    context["graph_counts"] = service.counts()
    return answer, context


def answer_question(question: str, service: Any) -> tuple[str, dict[str, Any], str]:
    """Use graph results first. If configured, ask an LLM only to synthesize that evidence."""
    answer, context = deterministic_answer(question, service)
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return answer, context, "Graph-grounded mode"

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are LaunchLens, a release-readiness and dependency-impact agent. Answer only from the supplied live FalkorDB graph evidence. "
                        "Do not invent tasks, relationships, statuses, or decisions. If evidence is insufficient, say so. "
                        "Give a concise recommendation and explicitly cite task or decision titles used as evidence. "
                        "The relationship (Task)-[:DEPENDS_ON]->(Task) means the first task requires the second task to finish first."
                    ),
                },
                {"role": "user", "content": f"Question: {question}\n\nLive graph evidence (JSON):\n{json.dumps(context, ensure_ascii=False, default=str)}"},
            ],
        )
        content = response.choices[0].message.content
        if content and content.strip():
            return content.strip(), context, "LLM synthesis + FalkorDB evidence"
    except Exception as exc:
        context["llm_fallback_reason"] = str(exc)[:300]
    return answer, context, "Graph-grounded mode (LLM unavailable; deterministic fallback used)"
