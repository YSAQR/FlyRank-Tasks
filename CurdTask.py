import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from repository import TaskRepository, InMemoryTaskRepository, PostgresTaskRepository

# Load environment variables from .env file
load_dotenv()

# Build database connection URI from environment variables or DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "db")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "tasks_db")
    DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{db}"

# ==============================================================================
# REPOSITORY SWAP POINT
# Decoupled Architecture: To swap back to In-Memory, change only this line:
# repository: TaskRepository = InMemoryTaskRepository()
# ==============================================================================
repository: TaskRepository = PostgresTaskRepository(DATABASE_URL)


app = FastAPI(
    title="To-Do List API",
    description="A simple CRUD API for managing tasks built with FastAPI and PostgreSQL.",
    version="1.0.0",
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
    return repository.get_all()


# 2. READ SINGLE TASK BY ID (GET)
@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
def get_task(task_id: int):
    """Retrieve a specific task by its ID."""
    task = repository.get_by_id(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    return task


# 3. CREATE TASK (POST)
@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Tasks"],
)
def create_task(task_data: TaskCreate):
    """Create a new task."""
    return repository.create(
        title=task_data.title,
        description=task_data.description,
        completed=task_data.completed,
    )


# 4. UPDATE TASK (PUT)
@app.put("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
def update_task(task_id: int, task_data: TaskUpdate):
    """Update an existing task by ID."""
    updated_task = repository.update(
        task_id=task_id,
        title=task_data.title,
        description=task_data.description,
        completed=task_data.completed,
    )
    if updated_task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    return updated_task


# 5. DELETE TASK (DELETE)
@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Tasks"],
)
def delete_task(task_id: int):
    """Delete a task by ID."""
    deleted = repository.delete(task_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found",
        )
    return None