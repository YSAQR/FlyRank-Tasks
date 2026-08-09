# FlyRank-Tasks

## To-Do List API (SQLite Integrated)

This is a CRUD API for managing tasks, built with FastAPI and SQLite.

### Why SQLite was chosen
SQLite is a lightweight, serverless database that stores everything in a single file on disk. It requires no installation or background processes, making it perfect for simple applications where we just want our data to survive server restarts without complex setup.

### Where the database file is stored
The database is stored locally in a file named `tasks.db` in the root directory of the project. It is automatically created the first time the application runs.

### How to start the project
Run the following command to start the FastAPI server using Uvicorn:
```bash
uvicorn CurdTask:app --reload
```
Once running, you can access the API documentation at `http://127.0.0.1:8000/docs`.

### Database Viewer Screenshot
![SQLite DB Browser Screenshot](./db_viewer.png)

### Example SQL Query
Here is an example query used to fetch all completed tasks:
```sql
SELECT * FROM tasks WHERE completed = 1;
```
