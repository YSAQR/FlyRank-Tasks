from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import os
import psycopg2
from psycopg2.extras import RealDictCursor


class TaskRepository(ABC):
    """Abstract Repository interface for Task storage."""

    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        """Retrieve all tasks."""
        pass

    @abstractmethod
    def get_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a task by ID."""
        pass

    @abstractmethod
    def create(self, title: str, description: Optional[str] = None, completed: bool = False) -> Dict[str, Any]:
        """Create a new task."""
        pass

    @abstractmethod
    def update(
        self,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update an existing task by ID."""
        pass

    @abstractmethod
    def delete(self, task_id: int) -> bool:
        """Delete a task by ID."""
        pass


class InMemoryTaskRepository(TaskRepository):
    """In-Memory implementation of TaskRepository."""

    def __init__(self):
        self._tasks: Dict[int, Dict[str, Any]] = {
            1: {"id": 1, "title": "Learn FastAPI", "description": "Build a simple CRUD API", "completed": True},
            2: {"id": 2, "title": "Build a To-Do App", "description": "Connect FastAPI to frontend", "completed": False},
            3: {"id": 3, "title": "In-Memory Demo", "description": "Testing repository abstraction", "completed": False},
        }
        self._next_id: int = 4

    def get_all(self) -> List[Dict[str, Any]]:
        return list(self._tasks.values())

    def get_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        return self._tasks.get(task_id)

    def create(self, title: str, description: Optional[str] = None, completed: bool = False) -> Dict[str, Any]:
        task = {
            "id": self._next_id,
            "title": title,
            "description": description,
            "completed": completed,
        }
        self._tasks[self._next_id] = task
        self._next_id += 1
        return task

    def update(
        self,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> Optional[Dict[str, Any]]:
        if task_id not in self._tasks:
            return None
        task = self._tasks[task_id]
        if title is not None:
            task["title"] = title
        if description is not None:
            task["description"] = description
        if completed is not None:
            task["completed"] = completed
        return task

    def delete(self, task_id: int) -> bool:
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False


class PostgresTaskRepository(TaskRepository):
    """PostgreSQL implementation of TaskRepository."""

    def __init__(self, connection_uri: str):
        self.connection_uri = connection_uri
        self._ensure_table_exists()

    def _get_connection(self):
        return psycopg2.connect(self.connection_uri, cursor_factory=RealDictCursor)

    def _ensure_table_exists(self):
        """Create table if it does not exist."""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS tasks (
                            id SERIAL PRIMARY KEY,
                            title VARCHAR(255) NOT NULL,
                            description TEXT,
                            completed BOOLEAN NOT NULL DEFAULT FALSE
                        );
                    """)
                conn.commit()
        except Exception as e:
            print(f"[PostgresTaskRepository] Table initialization warning/deferred: {e}")

    def get_all(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, title, description, completed FROM tasks ORDER BY id ASC;")
                rows = cur.fetchall()
                return [dict(r) for r in rows]

    def get_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, title, description, completed FROM tasks WHERE id = %s;", (task_id,))
                row = cur.fetchone()
                return dict(row) if row else None

    def create(self, title: str, description: Optional[str] = None, completed: bool = False) -> Dict[str, Any]:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO tasks (title, description, completed)
                    VALUES (%s, %s, %s)
                    RETURNING id, title, description, completed;
                    """,
                    (title, description, completed),
                )
                new_row = cur.fetchone()
                conn.commit()
                return dict(new_row)

    def update(
        self,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> Optional[Dict[str, Any]]:
        existing = self.get_by_id(task_id)
        if not existing:
            return None

        new_title = title if title is not None else existing["title"]
        new_desc = description if description is not None else existing["description"]
        new_comp = completed if completed is not None else existing["completed"]

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE tasks
                    SET title = %s, description = %s, completed = %s
                    WHERE id = %s
                    RETURNING id, title, description, completed;
                    """,
                    (new_title, new_desc, new_comp, task_id),
                )
                updated_row = cur.fetchone()
                conn.commit()
                return dict(updated_row) if updated_row else None

    def delete(self, task_id: int) -> bool:
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM tasks WHERE id = %s RETURNING id;", (task_id,))
                deleted_row = cur.fetchone()
                conn.commit()
                return bool(deleted_row)
