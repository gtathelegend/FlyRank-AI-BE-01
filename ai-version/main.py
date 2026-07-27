import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, StrictStr, StrictBool
from typing import Optional, List

app = FastAPI(
    title="Task API - AI Version",
    version="1.0",
    description="An alternative AI-generated implementation of the task management API.",
)

# In-memory storage
tasks = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Read a book", "done": True},
    {"id": 3, "title": "Write some code", "done": False}
]

# Pydantic schemas for input/output and automatic validation
class Task(BaseModel):
    id: int
    title: str
    done: bool

class TaskCreate(BaseModel):
    title: StrictStr = Field(..., description="The title of the task")

class TaskUpdate(BaseModel):
    title: Optional[StrictStr] = Field(None, description="The updated title of the task")
    done: Optional[StrictBool] = Field(None, description="The updated status of the task")

class ErrorResponse(BaseModel):
    error: str

# Custom exception handler to return 400 Bad Request instead of FastAPI's default 422 for validation errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    if errors:
        err = errors[0]
        loc = err.get("loc", [])
        field = loc[-1] if loc else "field"
        msg = err.get("msg", "Invalid value")
        err_type = err.get("type", "")
        # Generate custom friendly error responses matching spec format
        if err_type == "missing":
            return JSONResponse(status_code=400, content={"error": f"Title is required"})
        elif "string" in err_type:
            return JSONResponse(status_code=400, content={"error": "Title must be a string"})
        elif "bool" in err_type:
            return JSONResponse(status_code=400, content={"error": "Done must be a boolean"})
        return JSONResponse(status_code=400, content={"error": f"Invalid value for {field}: {msg}"})
    return JSONResponse(status_code=400, content={"error": "Invalid request body"})

@app.get("/", response_model=dict, summary="Root Metadata")
def read_root():
    return {
        "name": "Task API - AI Version",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health", response_model=dict, summary="Health Status")
def read_health():
    return {"status": "ok"}

@app.get("/tasks", response_model=List[Task], summary="List Tasks")
def get_tasks(done: Optional[bool] = None, search: Optional[str] = None):
    filtered_tasks = tasks
    if done is not None:
        filtered_tasks = [t for t in filtered_tasks if t["done"] == done]
    if search is not None:
        search_term = search.lower()
        filtered_tasks = [t for t in filtered_tasks if search_term in t["title"].lower()]
    return filtered_tasks

@app.get("/tasks/{task_id}", response_model=Task, summary="Get Task by ID")
def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})

@app.post("/tasks", response_model=Task, status_code=201, summary="Create Task")
def create_task(task_input: TaskCreate):
    if not task_input.title.strip():
        return JSONResponse(status_code=400, content={"error": "Title cannot be empty or whitespace only"})
    
    next_id = max(t["id"] for t in tasks) + 1 if tasks else 1
    new_task = {
        "id": next_id,
        "title": task_input.title,
        "done": False
    }
    tasks.append(new_task)
    return new_task

@app.put("/tasks/{task_id}", response_model=Task, summary="Update Task")
def update_task(task_id: int, task_input: TaskUpdate):
    target_task = None
    for t in tasks:
        if t["id"] == task_id:
            target_task = t
            break
    if not target_task:
        return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})
    
    # Check if empty body is sent or no changes
    if task_input.title is None and task_input.done is None:
        return JSONResponse(status_code=400, content={"error": "At least one update field must be provided"})
    
    if task_input.title is not None:
        if not task_input.title.strip():
            return JSONResponse(status_code=400, content={"error": "Title cannot be empty or whitespace only"})
        target_task["title"] = task_input.title
        
    if task_input.done is not None:
        target_task["done"] = task_input.done
        
    return target_task

@app.delete("/tasks/{task_id}", status_code=204, summary="Delete Task")
def delete_task(task_id: int):
    target_task = None
    for t in tasks:
        if t["id"] == task_id:
            target_task = t
            break
    if not target_task:
        return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})
    
    tasks.remove(target_task)
    return Response(status_code=204)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
