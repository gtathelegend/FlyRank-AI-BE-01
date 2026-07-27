import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

app = FastAPI()

# In-memory storage for tasks
tasks = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Read a book", "done": True},
    {"id": 3, "title": "Write some code", "done": False}
]

@app.get("/")
def read_root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health")
def read_health():
    return {"status": "ok"}

@app.get("/tasks")
def get_tasks():
    return tasks

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    return JSONResponse(status_code=404, content={"error": f"Task {task_id} not found"})

@app.post("/tasks")
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

@app.put("/tasks/{task_id}")
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

@app.delete("/tasks/{task_id}")
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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
