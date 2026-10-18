from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

from agent import answer_question
from graph_service import GraphService
from visualization import build_graphviz_dot

load_dotenv()
st.set_page_config(page_title="LaunchLens | Release intelligence", page_icon="🚦", layout="wide")

st.markdown(
    """
    <style>
      .block-container {max-width: 1320px; padding-top: 1.35rem; padding-bottom: 3rem;}
      div[data-testid="stMetric"] {background: linear-gradient(145deg, rgba(34,55,86,.055), rgba(14,165,160,.045)); border: 1px solid rgba(100,116,139,.22); padding: 16px 18px; border-radius: 16px;}
      .launchlens-kicker {font-size:.76rem; letter-spacing:.14em; text-transform:uppercase; color:#0d9488; font-weight:750; margin-bottom:.25rem;}
      .launchlens-subtitle {color: #718096; margin-top: -10px; margin-bottom: 20px; font-size: 1.02rem;}
      .launchlens-hero {border:1px solid rgba(13,148,136,.28); border-radius:20px; padding:22px 24px; background:linear-gradient(115deg, rgba(13,148,136,.09), rgba(59,130,246,.04)); margin:0 0 18px 0;}
      .launchlens-hero h3 {margin:0 0 6px 0; letter-spacing:-.02em;}
      .launchlens-hero p {margin:0; color:inherit; opacity:.8;}
      .small-muted {color:#718096; font-size:.88rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_service() -> GraphService:
    return GraphService()


st.markdown('<div class="launchlens-kicker">Graph-powered release intelligence</div>', unsafe_allow_html=True)
st.title("🚦 LaunchLens")
st.markdown("<p class='launchlens-subtitle'>See the blast radius before you ship.</p>", unsafe_allow_html=True)
st.markdown(
    "<div class='launchlens-hero'><h3>Know whether a release is actually ready.</h3>"
    "<p>Trace hidden prerequisites across teams, see what a change would unblock, and recover the decisions behind release checks — with every answer grounded in FalkorDB relationships.</p></div>",
    unsafe_allow_html=True,
)

try:
    service = get_service()
    service.wait_until_ready()
    seeded = service.ensure_demo_data()
except Exception as exc:
    st.error("LaunchLens cannot reach FalkorDB yet.")
    st.code(str(exc))
    st.markdown("**Start locally:** open a terminal in the project folder and run `docker compose up -d falkordb`, then `pip install -r requirements.txt` and `streamlit run app.py`.")
    st.markdown("FalkorDB Browser, when available locally: [http://localhost:3000](http://localhost:3000)")
    st.stop()

if seeded:
    st.toast("Created synthetic demo graph in FalkorDB", icon="✅")

counts = service.counts()
tasks = service.list_tasks()
ready = service.get_ready_tasks()
blocked = service.get_blocked_tasks()
decisions = service.list_decisions()
release_task = next((task for task in tasks if "release candidate" in task["title"].lower() or "release gate" in task["title"].lower()), None)
release_blockers = service.get_blockers_for_task(release_task["id"]) if release_task else []
if not release_task:
    release_label = "NO GATE"
elif release_task["status"] == "done" and release_blockers:
    # Graph consistency takes precedence over a manually edited status flag.
    release_label = "NOT READY"
elif release_task["status"] == "done":
    release_label = "APPROVED"
elif release_task["status"] == "blocked" or release_blockers:
    release_label = "NOT READY"
else:
    release_label = "READY FOR REVIEW"

with st.sidebar:
    st.header("Graph status")
    st.success(f"Connected · `{os.getenv('FALKORDB_GRAPH', 'launchlens')}`")
    st.caption(f"FalkorDB endpoint: {os.getenv('FALKORDB_HOST', 'localhost')}:{os.getenv('FALKORDB_PORT', '6379')}")
    st.metric("Graph nodes", counts["tasks"] + counts["decisions"] + 1)
    st.metric("Relationships", counts["dependencies"] + counts["decision_links"] + counts["tasks"])
    st.caption("Synthetic data is used by default. No private data is loaded.")
    st.divider()
    st.markdown("**Submission track**")
    st.write("Agents That Act on Connected Data")
    st.caption("Optional OpenAI synthesis is enabled only when OPENAI_API_KEY is configured.")
    if st.button("Reset local demo graph", help="Deletes every node in the configured LaunchLens graph and recreates the fictional sample."):
        st.session_state["confirm_reset"] = True
    if st.session_state.get("confirm_reset"):
        st.warning("This clears the configured graph before recreating sample data.")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Confirm reset", type="primary"):
                service.reset_demo_graph()
                st.session_state["confirm_reset"] = False
                st.session_state.pop("agent_answer", None)
                st.rerun()
        with col_b:
            if st.button("Cancel"):
                st.session_state["confirm_reset"] = False
                st.rerun()

metric_cols = st.columns(4)
metric_cols[0].metric("Tracked tasks", counts["tasks"])
metric_cols[1].metric("Completed", sum(1 for t in tasks if t["status"] == "done"))
metric_cols[2].metric("Ready now", len(ready))
metric_cols[3].metric("Release gate", release_label, f"{len(release_blockers)} upstream blockers" if release_blockers else None)

if release_label == "NOT READY":
    if release_task and release_task["status"] == "done" and release_blockers:
        st.error(f"**Inconsistent release state.** The release task is marked done, but FalkorDB still shows {len(release_blockers)} unfinished prerequisite(s). LaunchLens will not treat that status flag as approval.")
    else:
        st.warning(f"**Release candidate is not ready.** The graph traces {len(release_blockers)} unfinished prerequisite task(s) on paths to release approval. Ask LaunchLens **‘Can we release?’** to inspect the chain.")
elif release_label == "NO GATE":
    st.error("No release-approval task is linked to this project graph. Add a release gate and connect its required checks as prerequisites.")
elif release_label == "READY FOR REVIEW":
    st.success("**Release checks look clear in the current graph.** A human still needs to approve the release.")
else:
    st.success("**Release gate marked approved** in the graph. This records workflow state; it is not a production-safety guarantee.")

agent_tab, tasks_tab, decisions_tab, graph_tab = st.tabs(["Ask LaunchLens", "Task board", "Decision memory", "Graph evidence"])

with agent_tab:
    st.subheader("Ask about release readiness")
    st.write("Answers are grounded in live graph queries. Try a suggested prompt or ask your own question.")
    suggestions = [
        "Can we release?",
        "What gets unblocked if T2 is done?",
        "What is blocked and why?",
        "What decision should I remember about authentication?",
    ]
    prompt_grid = [st.columns(2), st.columns(2)]
    for i, prompt in enumerate(suggestions):
        if prompt_grid[i // 2][i % 2].button(prompt, key=f"suggest_{i}", use_container_width=True):
            st.session_state["agent_question"] = prompt
    with st.form("ask_form", clear_on_submit=False):
        question = st.text_input("Your question", key="agent_question", placeholder="e.g. Can we release? What gets unblocked if T2 is done?")
        ask = st.form_submit_button("Ask the graph", type="primary")
    if ask and question.strip():
        try:
            with st.spinner("Traversing live dependency and decision paths in FalkorDB…"):
                answer, context, mode = answer_question(question.strip(), service)
            st.session_state["agent_answer"] = {"question": question.strip(), "answer": answer, "context": context, "mode": mode}
        except Exception as exc:
            st.error("The graph question could not be completed. Your data was not intentionally reset.")
            st.code(str(exc))
    result = st.session_state.get("agent_answer")
    if result:
        st.markdown("#### LaunchLens's answer")
        st.caption(result["mode"])
        st.markdown(result["answer"])
        with st.expander("Inspect the exact graph evidence retrieved"):
            st.json(result["context"])
    else:
        st.info("Start with **Can we release?** or **What gets unblocked if T2 is done?** The agent will query the current graph and explain its recommendation.")

with tasks_tab:
    st.subheader("Release task board")
    st.caption("Readiness is calculated from `DEPENDS_ON` relationships in FalkorDB. Tasks with unfinished prerequisites are not recommended as ready.")
    status_labels = {"todo": "To do", "in_progress": "In progress", "blocked": "Blocked", "done": "Done"}
    for status, title in [("in_progress", "In progress"), ("todo", "To do"), ("blocked", "Blocked"), ("done", "Done")]:
        section = [t for t in tasks if t["status"] == status]
        with st.expander(f"{title} · {len(section)}", expanded=(status in ("in_progress", "todo"))):
            if not section:
                st.caption("No tasks here.")
            for task in section:
                with st.container(border=True):
                    left, right = st.columns([4, 1])
                    left.markdown(f"**{task['title']}**  `{' · '.join([task['id'], task['priority'].upper(), task['owner']])}`")
                    left.write(task["description"])
                    deps = task["dependencies"]
                    if deps:
                        left.caption("Depends on: " + ", ".join(f"{d['title']} [{d['status']}]" for d in deps))
                    else:
                        left.caption("No prerequisites")
                    right.caption(f"Due {task['due_date']}")

    st.divider()
    st.markdown("#### Update a task")
    task_lookup = {f"{t['id']} — {t['title']}": t["id"] for t in tasks}
    with st.form("update_task_form"):
        chosen_task_label = st.selectbox("Task", list(task_lookup))
        new_status = st.selectbox("New status", ["todo", "in_progress", "blocked", "done"], format_func=lambda s: status_labels[s])
        update_submit = st.form_submit_button("Save status")
    if update_submit:
        try:
            service.update_task_status(task_lookup[chosen_task_label], new_status)
            st.session_state.pop("agent_answer", None)  # don't leave stale graph evidence on screen
            st.toast("Task status updated in FalkorDB.", icon="✅")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    with st.expander("Add a task"):
        with st.form("add_task_form"):
            new_title = st.text_input("Title")
            new_description = st.text_area("Description")
            c1, c2 = st.columns(2)
            new_priority = c1.selectbox("Priority", ["critical", "high", "medium", "low"], index=1)
            new_owner = c2.text_input("Owner", value="Unassigned")
            new_due = st.date_input("Due date")
            dependency_labels = st.multiselect("Must be finished first", list(task_lookup))
            add_submit = st.form_submit_button("Create graph task")
        if add_submit:
            try:
                new_id = service.add_task(new_title, new_description, new_priority, new_owner, new_due.isoformat(), [task_lookup[x] for x in dependency_labels])
                st.session_state.pop("agent_answer", None)
                st.toast(f"Created {new_id} and its graph relationships.", icon="✅")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

with decisions_tab:
    st.subheader("Decision memory")
    st.write("Decisions are stored as graph nodes and linked to every task they affect using `AFFECTS` relationships.")
    if decisions:
        for decision in decisions:
            with st.container(border=True):
                st.markdown(f"**{decision['title']}**  `{decision['id']}`")
                st.write(decision["details"])
                st.caption("Affects: " + ", ".join(decision["affected_tasks"]))
    else:
        st.info("No decisions yet. Add a decision below and link it to a task.")
    with st.expander("Record a decision"):
        with st.form("decision_form"):
            decision_title = st.text_input("Decision title")
            decision_details = st.text_area("What was decided and why?")
            affected_labels = st.multiselect("Tasks affected", list(task_lookup))
            save_decision = st.form_submit_button("Save decision to FalkorDB")
        if save_decision:
            try:
                decision_id = service.add_decision(decision_title, decision_details, [task_lookup[x] for x in affected_labels])
                st.session_state.pop("agent_answer", None)
                st.toast(f"Saved decision {decision_id} and linked it to the selected tasks.", icon="✅")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

with graph_tab:
    st.subheader("Why a graph is essential here")
    st.write("The agent's main behavior depends on traversing typed relationships. The following rows come directly from FalkorDB.")
    relationships = service.list_relationships()
    st.markdown("**Live relationship map**")
    st.caption("Node colors show task state (green = done, blue = in progress, gray = to do, red = blocked; yellow notes = decisions). Arrows follow the stored edge direction: a task points to its prerequisite; a decision points to tasks it affects.")
    st.graphviz_chart(build_graphviz_dot(tasks, relationships), use_container_width=True)
    st.markdown("**Raw graph rows** — available for exact inspection")
    with st.expander("Task dependency edges — `(Task)-[:DEPENDS_ON]->(Prerequisite Task)`"):
        if relationships["dependencies"]:
            st.dataframe(relationships["dependencies"], use_container_width=True, hide_index=True)
        else:
            st.caption("No dependency edges yet.")
    with st.expander("Decision memory edges — `(Decision)-[:AFFECTS]->(Task)`"):
        if relationships["decision_links"]:
            st.dataframe(relationships["decision_links"], use_container_width=True, hide_index=True)
        else:
            st.caption("No decision edges yet.")
    st.markdown("**Core graph logic**")
    st.code(
        "MATCH (p:Project)-[:HAS_TASK]->(t:Task)\n"
        "WHERE t.status IN ['todo', 'in_progress']\n"
        "OPTIONAL MATCH (t)-[:DEPENDS_ON]->(dep:Task)\n"
        "WITH t, collect(dep) AS deps\n"
        "WHERE all(dep IN deps WHERE dep.status = 'done')\n"
        "RETURN t.title, t.status, size(deps) AS prerequisites",
        language="cypher",
    )
    st.caption("If FalkorDB is removed, the readiness query, dependency-path explanations, and connected decision retrieval cannot run. There is no alternate local task database.")

st.divider()
st.caption("LaunchLens · Graph Hacks 2026 · Synthetic data · FalkorDB is the system of record")
