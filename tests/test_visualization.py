from visualization import build_graphviz_dot


def test_diagram_uses_returned_task_and_relationship_records():
    tasks = [
        {"id": "T2", "title": "Implement authentication service", "status": "in_progress"},
        {"id": "T3", "title": "Integrate sign-in UI", "status": "todo"},
    ]
    relationships = {
        "dependencies": [
            {"task_id": "T3", "task": "Integrate sign-in UI", "dependency_id": "T2", "depends_on": "Implement authentication service"}
        ],
        "decision_links": [
            {"decision_id": "D1", "decision": "Access tokens must be short-lived", "task_id": "T2", "task": "Implement authentication service"}
        ],
    }

    dot = build_graphviz_dot(tasks, relationships)
    assert '"task::T2"' in dot
    assert '"task::T3"' in dot
    assert '"decision::D1"' in dot
    assert 'label="depends on"' in dot
    assert 'label="affects"' in dot
    assert "[in progress]" in dot
    assert "Implement authentication service" in dot


def test_diagram_escapes_quoted_titles_instead_of_breaking_dot_syntax():
    dot = build_graphviz_dot(
        [{"id": "T9", "title": 'Check "release"\\gate', "status": "todo"}],
        {"dependencies": [], "decision_links": []},
    )
    assert r'Check \"release\"' in dot
    assert "digraph LaunchLens" in dot
    assert 'rankdir="TB"' in dot
    assert dot.rstrip().endswith("}")
