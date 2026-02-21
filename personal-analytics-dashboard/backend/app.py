from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.database import engine
from backend.models import Base

Base.metadata.create_all(bind=engine)

from backend.routes.tasks import router as tasks_router
from backend.routes.schedules import router as schedules_router
from backend.routes.feedback import router as feedback_router
from backend.routes.auth import router as auth_router

app = FastAPI(title="Personal Analytics Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

'''
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")
'''

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(tasks_router,     prefix="/tasks",     tags=["tasks"])
app.include_router(schedules_router, prefix="/schedules", tags=["schedules"])
app.include_router(feedback_router,  prefix="/feedback",  tags=["feedback"])