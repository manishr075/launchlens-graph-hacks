// LaunchLens — documented FalkorDB queries used by the application.
// Parameters are passed by the Python client; do not paste $parameters without values into the browser.

// 1. Find ready work and count unfinished downstream tasks for graph-aware prioritization.
MATCH (p:Project {id: $project_id})-[:HAS_TASK]->(t:Task)
WHERE t.status IN ['todo', 'in_progress']
OPTIONAL MATCH (t)-[:DEPENDS_ON]->(dep:Task)
WITH t, collect(dep) AS deps
WHERE all(dep IN deps WHERE dep.status = 'done')
OPTIONAL MATCH (downstream:Task)-[:DEPENDS_ON*1..]->(t)
WHERE downstream.id <> t.id AND downstream.status IN ['todo', 'in_progress', 'blocked']
WITH t, deps, count(DISTINCT downstream) AS downstream_count
RETURN t.id, t.title, t.status, t.priority, size(deps) AS dependency_count, downstream_count;

// 2. Find unfinished tasks that have an unfinished prerequisite at any depth.
MATCH (p:Project {id: $project_id})-[:HAS_TASK]->(t:Task)
WHERE t.status IN ['todo', 'in_progress']
MATCH (t)-[:DEPENDS_ON*1..]->(dep:Task)
WHERE dep.status <> 'done'
RETURN t.id, t.title, t.status, collect(DISTINCT dep.title) AS blockers
ORDER BY t.id;

// 3. Explain every unfinished prerequisite in a task's dependency chain.
MATCH (t:Task {id: $task_id})-[:DEPENDS_ON*1..]->(dep:Task)
WHERE dep.status <> 'done'
RETURN dep.id, dep.title, dep.status
ORDER BY dep.id;

// 4. Trace the downstream impact of completing a task: unfinished tasks whose dependency path leads to it.
MATCH (target:Task {id: $task_id}), (downstream:Task)
WHERE downstream.status <> 'done' AND downstream.id <> target.id
MATCH path = allShortestPaths((downstream)-[:DEPENDS_ON*1..]->(target))
WITH downstream, target, length(path) AS distance,
     collect(DISTINCT [n IN nodes(path) | n.title]) AS dependency_paths
OPTIONAL MATCH (downstream)-[:DEPENDS_ON]->(direct_dep:Task)
WITH downstream, target, distance, dependency_paths, collect(direct_dep) AS direct_deps
WITH downstream, target, distance, dependency_paths,
     (downstream.status IN ['todo', 'in_progress'] AND
      all(dep IN direct_deps WHERE dep.status = 'done' OR dep.id = target.id)) AS ready_if_target_done
OPTIONAL MATCH (d:Decision)-[:AFFECTS]->(downstream)
RETURN downstream.id, downstream.title, downstream.status, distance, dependency_paths,
       ready_if_target_done, collect(DISTINCT d.title) AS linked_decisions
ORDER BY distance, downstream.id;

// 5. Retrieve prior decisions and the tasks each affects.
MATCH (d:Decision)-[:AFFECTS]->(t:Task)
RETURN d.id, d.title, d.details, d.created_at, collect(DISTINCT t.title) AS affected_tasks
ORDER BY d.created_at DESC;

// 6. Show the complete dependency map.
MATCH (t:Task)-[:DEPENDS_ON]->(dep:Task)
RETURN t.id, t.title, dep.id, dep.title
ORDER BY t.id, dep.id;

// 7. Record a task status update.
MATCH (t:Task {id: $task_id})
SET t.status = $status, t.updated_at = $updated_at
RETURN t.id, t.status;
