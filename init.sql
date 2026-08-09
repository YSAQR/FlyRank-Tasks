-- Initialize schema for To-Do List Tasks
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    completed BOOLEAN NOT NULL DEFAULT FALSE
);

-- Seed initial tasks if table is empty
INSERT INTO tasks (title, description, completed)
SELECT 'Learn Docker & Postgres', 'Run Postgres in Docker container with volume persistence', true
WHERE NOT EXISTS (SELECT 1 FROM tasks);

INSERT INTO tasks (title, description, completed)
SELECT 'Build Repository Layer', 'Decouple database storage from FastAPI routes', false
WHERE NOT EXISTS (SELECT 1 FROM tasks WHERE title = 'Build Repository Layer');

INSERT INTO tasks (title, description, completed)
SELECT 'Prove Data Persistence', 'Restart containers and verify data remains intact', false
WHERE NOT EXISTS (SELECT 1 FROM tasks WHERE title = 'Prove Data Persistence');
