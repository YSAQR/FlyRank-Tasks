import sqlite3
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from contextlib import asynccontextmanager

# Database setup
DB_FILE = "tasks.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Create the table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN NOT NULL DEFAULT 0
        )
    ''')
    
    # Check if empty, insert 3 example tasks
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]
    
    if count == 0:
        example_tasks = [
            ("Learn FastAPI", "Build a simple CRUD API", True),
            ("Build a To-Do App", "Connect FastAPI to frontend", False),
            ("Learn SQLite", "Connect database to API", False)
        ]
        cursor.executemany(
            "INSERT INTO tasks (title, description, completed) VALUES (?, ?, ?)",
            example_tasks
        )
        conn.commit()
    conn.close()
    yield

app = FastAPI(
    title="To-Do List API",
    description="A simple CRUD API for managing tasks built with FastAPI.",
    version="1.0.0",
    lifespan=lifespan,
)


# Pydantic Schemas for Request & Response Data Validation
class TaskCreate(BaseModel):
    title: str = Field(..., json_schema_extra={"example": "Buy groceries"})
    description: Optional[str] = Field(None, json_schema_extra={"example": "Milk, Eggs, Bread"})
    completed: bool = Field(default=False)


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, json_schema_extra={"example": "Buy groceries and fruits"})
    description: Optional[str] = Field(None)
    completed: Optional[bool] = Field(None, json_schema_extra={"example": True})


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    completed: bool


# 1. READ ALL TASKS (GET)
@app.get("/tasks", response_model=List[TaskResponse], tags=["Tasks"])
def get_all_tasks():
    """Retrieve all tasks from the to-do list."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks")
    rows = cursor.fetchall()
    conn.close()
    
    tasks = []
    for row in rows:
        tasks.append(dict(row))
    return tasks


# 2. READ SINGLE TASK BY ID (GET)
@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
def get_task(task_id: int):
    """Retrieve a specific task by its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    return dict(row)


# 3. CREATE TASK (POST)
@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Tasks"],
)
def create_task(task_data: TaskCreate):
    """Create a new task."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO tasks (title, description, completed) VALUES (?, ?, ?)",
        (task_data.title, task_data.description, task_data.completed)
    )
    conn.commit()
    task_id = cursor.lastrowid
    
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    new_task = cursor.fetchone()
    conn.close()
    
    return dict(new_task)


# 4. UPDATE TASK (PUT)
@app.put("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
def update_task(task_id: int, task_data: TaskUpdate):
    """Update an existing task by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    existing_task = cursor.fetchone()
    
    if existing_task is None:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    
    # Use existing values if not provided
    title = task_data.title if task_data.title is not None else existing_task["title"]
    description = task_data.description if task_data.description is not None else existing_task["description"]
    completed = task_data.completed if task_data.completed is not None else existing_task["completed"]
    
    cursor.execute(
        "UPDATE tasks SET title = ?, description = ?, completed = ? WHERE id = ?",
        (title, description, completed, task_id)
    )
    conn.commit()
    
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    updated_task = cursor.fetchone()
    conn.close()
    
    return dict(updated_task)


# 5. DELETE TASK (DELETE)
@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Tasks"],
)
def delete_task(task_id: int):
    """Delete a task by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    
    if row is None:
        conn.close()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
        
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    
    return None