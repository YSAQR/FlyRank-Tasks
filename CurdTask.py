from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI(
    title="To-Do List API",
    description="A simple CRUD API for managing tasks built with FastAPI.",
    version="1.0.0",
)


# Pydantic Schemas for Request & Response Data Validation
class TaskCreate(BaseModel):
    title: str = Field(..., example="Buy groceries")
    description: Optional[str] = Field(None, example="Milk, Eggs, Bread")
    completed: bool = Field(default=False)


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, example="Buy groceries and fruits")
    description: Optional[str] = Field(None)
    completed: Optional[bool] = Field(None, example=True)


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    completed: bool


# In-memory Task Database
tasks_db: List[dict] = [
    {
        "id": 1,
        "title": "Learn FastAPI",
        "description": "Build a simple CRUD API",
        "completed": True,
    },
    {
        "id": 2,
        "title": "Build a To-Do App",
        "description": "Connect FastAPI to frontend",
        "completed": False,
    },
]

task_id_counter = 3


# 1. READ ALL TASKS (GET)
@app.get("/tasks", response_model=List[TaskResponse], tags=["Tasks"])
def get_all_tasks():
    """Retrieve all tasks from the to-do list."""
    return tasks_db


# 2. READ SINGLE TASK BY ID (GET)
@app.get("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
def get_task(task_id: int):
    """Retrieve a specific task by its ID."""
    for task in tasks_db:
        if task["id"] == task_id:
            return task
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task with ID {task_id} not found",
    )


# 3. CREATE TASK (POST)
@app.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Tasks"],
)
def create_task(task_data: TaskCreate):
    """Create a new task."""
    global task_id_counter
    new_task = {
        "id": task_id_counter,
        "title": task_data.title,
        "description": task_data.description,
        "completed": task_data.completed,
    }
    tasks_db.append(new_task)
    task_id_counter += 1
    return new_task


# 4. UPDATE TASK (PUT)
@app.put("/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
def update_task(task_id: int, task_data: TaskUpdate):
    """Update an existing task by ID."""
    for task in tasks_db:
        if task["id"] == task_id:
            if task_data.title is not None:
                task["title"] = task_data.title
            if task_data.description is not None:
                task["description"] = task_data.description
            if task_data.completed is not None:
                task["completed"] = task_data.completed
            return task
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task with ID {task_id} not found",
    )


# 5. DELETE TASK (DELETE)
@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Tasks"],
)
def delete_task(task_id: int):
    """Delete a task by ID."""
    for index, task in enumerate(tasks_db):
        if task["id"] == task_id:
            tasks_db.pop(index)
            return None
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Task with ID {task_id} not found",
    )