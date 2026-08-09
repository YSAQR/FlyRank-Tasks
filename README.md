# FlyRank-Tasks: To-Do List API (PostgreSQL + Docker + Repository Pattern)

A robust, production-grade CRUD API for task management built with **FastAPI**, **PostgreSQL**, **Docker & Docker Compose**, and the **Repository Pattern**.

---

## 🏛️ Decoupled Architecture & The Repository Pattern

This project implements the **Repository Pattern** to separate data access logic from business rules and HTTP routes:

```
[ FastAPI Routes & Controllers ]  <-- Unchanged
              |
              v
   [ TaskRepository Interface ]
         /           \
        v             v
[ InMemoryRepo ]   [ PostgresRepo ]  <-- Storage Swapped (1 line edit)
```

### ⚡ Proof of Architecture (Swapping Storage in 1 Line)

The FastAPI routes and Pydantic schemas in `CurdTask.py` depend exclusively on the abstract `TaskRepository` interface defined in `repository.py`.

To switch the underlying storage from **PostgreSQL** back to **In-Memory**, you only change **one single line** in `CurdTask.py`:

```python
# To use In-Memory storage:
repository: TaskRepository = InMemoryTaskRepository()

# To use PostgreSQL storage:
repository: TaskRepository = PostgresTaskRepository(DATABASE_URL)
```

**Zero changes** were made to the route handlers (`/tasks` GET, POST, PUT, DELETE) or Pydantic schemas when migrating to PostgreSQL.

---

## 🚀 Quick Start with Docker Compose

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) with Docker Compose v2+

### 1. Environment Configuration
Create a `.env` file from `.env.example`:
```bash
cp .env.example .env
```

The default `.env` contents:
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=tasks_db
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE_URL=postgresql://postgres:postgres@db:5432/tasks_db
```

### 2. Start the Stack (One Command)
Run the following command to build and launch both the PostgreSQL database and FastAPI application containers:
```bash
docker compose up -d --build
```

Access the interactive API documentation (Swagger UI) at:
👉 `http://localhost:8000/docs`

---

## 💾 Data Persistence Across Restarts

Data is stored in a dedicated Docker named volume (`postgres_data`) managed by PostgreSQL in the database container.

### Step-by-Step Persistence Verification

#### Step 1: Create a new task via HTTP POST
```bash
curl -X POST "http://localhost:8000/tasks" \
     -H "Content-Type: application/json" \
     -d '{"title": "Persistent Task", "description": "This task must survive stack restarts", "completed": false}'
```

Response:
```json
{
  "id": 4,
  "title": "Persistent Task",
  "description": "This task must survive stack restarts",
  "completed": false
}
```

#### Step 2: Stop and remove containers
```bash
docker compose down
```

#### Step 3: Start containers back up
```bash
docker compose up -d
```

#### Step 4: Verify task persistence via HTTP GET
```bash
curl -X GET "http://localhost:8000/tasks"
```

The newly created `"Persistent Task"` (id 4) is returned, proving that data survives complete application and container destruction because of the `postgres_data` volume.

---

## 📁 Project Structure

```text
.
├── .env                # Local database credentials (Gitignored)
├── .env.example        # Committed template for environment configuration
├── .gitignore          # Rules for ignoring secrets, caches, and DB files
├── CurdTask.py          # FastAPI application entrypoint & API routes
├── Dockerfile          # Container configuration for FastAPI service
├── README.md           # Documentation and architecture breakdown
├── docker-compose.yml  # Multi-container orchestration (App + Postgres)
├── init.sql            # Database schema initialization & initial seed data
├── repository.py       # TaskRepository interface, InMemoryRepo, & PostgresRepo
└── requirements.txt    # Python dependencies
```
