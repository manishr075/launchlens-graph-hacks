"""Build a Graphviz diagram from records fetched from FalkorDB."""
from __future__ import annotations

import json
from typing import Any

STATUS_COLORS = {
    "done": "#dcfce7",
    "in_progress": "#dbeafe",
    "todo": "#f1f5f9",
    "blocked": "#fee2e2",
}


def _dot_string(value: Any) -> str:
    """Quote dynamic strings for Graphviz DOT labels and attributes."""
    return json.dumps(str(value), ensure_ascii=False)


def build_graphviz_dot(
    tasks: list[dict[str, Any]], relationships: dict[str, list[dict[str, str]]]
) -> str:
    """Create a dependency/decision map from graph query results, not hard-coded edges."""
    lines = [
        "digraph LaunchLens {",
        '  graph [rankdir="TB", bgcolor="transparent", pad="0.2", nodesep="0.45", ranksep="0.8"];',
        '  node [fontname="Arial", fontsize="10", penwidth="1.2"];',
        '  edge [fontname="Arial", fontsize="9", arrowsize="0.75"];',
    ]

    for task in tasks:
        task_id = str(task["id"])
        label = f'{task_id}\n{task["title"]}\n[{task["status"].replace("_", " ")}]'
        fill = STATUS_COLORS.get(str(task.get("status", "")), "#f8fafc")
        lines.append(
            f'  {_dot_string("task::" + task_id)} '
            f'[label={_dot_string(label)}, shape="box", style="rounded,filled", '
            f'fillcolor={_dot_string(fill)}, color="#94a3b8"];'
        )

    decision_titles: dict[str, str] = {}
    for edge in relationships.get("decision_links", []):
        decision_titles[str(edge["decision_id"])] = str(edge["decision"])
    for decision_id, title in sorted(decision_titles.items()):
        decision_label = decision_id + "\n" + title
        lines.append(
            f'  {_dot_string("decision::" + decision_id)} '
            f'[label={_dot_string(decision_label)}, shape="note", '
            'style="filled", fillcolor="#fef3c7", color="#d97706"];'
        )

    for edge in relationships.get("dependencies", []):
        lines.append(
            f'  {_dot_string("task::" + str(edge["task_id"]))} -> '
            f'{_dot_string("task::" + str(edge["dependency_id"]))} '
            '[label="depends on", color="#64748b", fontcolor="#475569"];'
        )
    for edge in relationships.get("decision_links", []):
        lines.append(
            f'  {_dot_string("decision::" + str(edge["decision_id"]))} -> '
            f'{_dot_string("task::" + str(edge["task_id"]))} '
            '[label="affects", style="dashed", color="#d97706", fontcolor="#92400e"];'
        )

    lines.append("}")
    return "\n".join(lines)
