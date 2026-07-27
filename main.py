import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI(
    title="Task API",
    version="1.0",
    description="A simple, in-memory CRUD API for managing tasks.",
)

# In-memory storage for tasks
tasks = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Read a book", "done": True},
    {"id": 3, "title": "Write some code", "done": False}
]

# Pydantic schemas for documentation
class Task(BaseModel):
    id: int = Field(..., description="The unique integer ID of the task")
    title: str = Field(..., description="The title of the task")
    done: bool = Field(..., description="The status of the task")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message details")

@app.get(
    "/",
    summary="Get API Metadata",
    description="Returns metadata about the Task API, including name, version, and endpoints.",
    responses={
        200: {
            "description": "API metadata returned successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "name": "Task API",
                        "version": "1.0",
                        "endpoints": ["/tasks"]
                    }
                }
            }
        }
    }
)
def read_root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get(
    "/health",
    summary="Check API Health Status",
    description="Returns the health status of the server.",
    responses={
        200: {
            "description": "Server health is okay.",
            "content": {
                "application/json": {
                    "example": {"status": "ok"}
                }
            }
        }
    }
)
def read_health():
    return {"status": "ok"}

@app.get(
    "/tasks",
    summary="List All Tasks",
    description="Retrieves a list of all existing tasks stored in-memory.",
    response_model=List[Task],
    responses={
        200: {
            "description": "Successfully retrieved task list."
        }
    }
)
def get_tasks():
    return tasks

@app.get(
    "/tasks/{task_id}",
    summary="Retrieve a Task by ID",
    description="Fetches a specific task using its unique integer ID.",
    response_model=Task,
    responses={
        200: {
            "description": "Successfully retrieved task."
        },
        404: {
            "model": ErrorResponse,
            "description": "Task not found."
        }
    }
)
def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})

@app.post(
    "/tasks",
    summary="Create a New Task",
    description="Creates a new task with an auto-incremented ID and done set to False.",
    response_model=Task,
    status_code=201,
    responses={
        201: {
            "description": "Task successfully created."
        },
        400: {
            "model": ErrorResponse,
            "description": "Missing, empty, whitespace-only, or invalid title format."
        }
    }
)
async def create_task(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})

    if "title" not in body:
        return JSONResponse(status_code=400, content={"error": "Title is required"})

    title = body["title"]
    if not isinstance(title, str):
        return JSONResponse(status_code=400, content={"error": "Title must be a string"})

    if not title.strip():
        return JSONResponse(status_code=400, content={"error": "Title cannot be empty or whitespace only"})

    next_id = max(t["id"] for t in tasks) + 1 if tasks else 1
    new_task = {
        "id": next_id,
        "title": title,
        "done": False
    }
    tasks.append(new_task)
    return JSONResponse(status_code=201, content=new_task)

@app.put(
    "/tasks/{task_id}",
    summary="Update a Task by ID",
    description="Updates the title, done status, or both fields of a specific task.",
    response_model=Task,
    responses={
        200: {
            "description": "Task successfully updated."
        },
        400: {
            "model": ErrorResponse,
            "description": "No valid fields provided, invalid title format, or non-boolean done state."
        },
        404: {
            "model": ErrorResponse,
            "description": "Task not found."
        }
    }
)
async def update_task(task_id: int, request: Request):
    target_task = None
    for task in tasks:
        if task["id"] == task_id:
            target_task = task
            break
    if not target_task:
        return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON body"})

    if not body:
        return JSONResponse(status_code=400, content={"error": "At least one update field must be provided"})

    has_title = "title" in body
    has_done = "done" in body

    if not has_title and not has_done:
        return JSONResponse(status_code=400, content={"error": "At least one update field must be provided"})

    if has_title:
        title = body["title"]
        if not isinstance(title, str):
            return JSONResponse(status_code=400, content={"error": "Title must be a string"})
        if not title.strip():
            return JSONResponse(status_code=400, content={"error": "Title cannot be empty or whitespace only"})

    if has_done:
        done = body["done"]
        if not isinstance(done, bool):
            return JSONResponse(status_code=400, content={"error": "Done must be a boolean"})

    if has_title:
        target_task["title"] = body["title"]
    if has_done:
        target_task["done"] = body["done"]

    return JSONResponse(status_code=200, content=target_task)

@app.delete(
    "/tasks/{task_id}",
    summary="Delete a Task by ID",
    description="Deletes a specific task from in-memory storage. Returns 204 No Content.",
    status_code=204,
    responses={
        204: {
            "description": "Task successfully deleted."
        },
        404: {
            "model": ErrorResponse,
            "description": "Task not found."
        }
    }
)
def delete_task(task_id: int):
    target_task = None
    for task in tasks:
        if task["id"] == task_id:
            target_task = task
            break
    if not target_task:
        return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})

    tasks.remove(target_task)
    return Response(status_code=204)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Task API",
        version="1.0",
        description="A simple, in-memory CRUD API for managing tasks.",
        routes=app.routes,
    )
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}
    if "schemas" not in openapi_schema["components"]:
        openapi_schema["components"]["schemas"] = {}

    openapi_schema["components"]["schemas"]["TaskCreateRequest"] = {
        "type": "object",
        "required": ["title"],
        "properties": {
            "title": {
                "type": "string",
                "description": "The title of the new task"
            }
        }
    }

    openapi_schema["components"]["schemas"]["TaskUpdateRequest"] = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "The updated title of the task"
            },
            "done": {
                "type": "boolean",
                "description": "The updated done status of the task"
            }
        }
    }

    if "/tasks" in openapi_schema["paths"]:
        if "post" in openapi_schema["paths"]["/tasks"]:
            openapi_schema["paths"]["/tasks"]["post"]["requestBody"] = {
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/TaskCreateRequest"}
                    }
                },
                "required": True
            }

    if "/tasks/{task_id}" in openapi_schema["paths"]:
        if "put" in openapi_schema["paths"]["/tasks/{task_id}"]:
            openapi_schema["paths"]["/tasks/{task_id}"]["put"]["requestBody"] = {
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/TaskUpdateRequest"}
                    }
                },
                "required": True
            }

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
