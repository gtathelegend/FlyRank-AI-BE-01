import uvicorn
from fastapi import FastAPI, Request
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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
