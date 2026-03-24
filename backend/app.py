import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:1420",
        "http://127.0.0.1:1420",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "tauri://localhost",
        "http://tauri.localhost",
    ],  # Web + Tauri dev/prod origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(tasks_router,     prefix="/tasks",     tags=["tasks"])
app.include_router(schedules_router, prefix="/schedules", tags=["schedules"])
app.include_router(feedback_router,  prefix="/feedback",  tags=["feedback"])

# ── SPA (Vite build): same origin as API on :8000 — no separate Vite server needed ──
_REPO_ROOT = Path(__file__).resolve().parent.parent
_FRONTEND_DIST = _REPO_ROOT / "web" / "react-version" / "dist"
if _FRONTEND_DIST.is_dir():
    app.mount(
        "/",
        StaticFiles(directory=str(_FRONTEND_DIST), html=True),
        name="spa",
    )
else:
    logging.getLogger(__name__).warning(
        "web/react-version/dist missing — run `npm run build` in web/react-version to serve the UI on :8000"
    )