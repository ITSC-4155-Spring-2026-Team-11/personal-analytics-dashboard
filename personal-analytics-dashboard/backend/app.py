from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


from backend.routes.tasks import router as tasks_router
from backend.routes.schedules import router as schedules_router
from backend.routes.feedback import router as feedback_router

app = FastAPI(title="Personal Analytics Dashboard API")

# Allow web client (index.html) to call the API from a browser.
# In production you would lock this down to your domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")

app.include_router(tasks_router, prefix="/tasks", tags=["tasks"])
app.include_router(schedules_router, prefix="/schedules", tags=["schedules"])
app.include_router(feedback_router, prefix="/feedback", tags=["feedback"])
