from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .db import apply_seed_if_needed, engine
from .models import Base
from .routers import action_items as action_items_router
from .routers import notes as notes_router
from .routers import tags as tags_router

app = FastAPI(title="Modern Software Dev Starter (Week 5)")

# Ensure data dir exists
Path("data").mkdir(parents=True, exist_ok=True)

# Mount static frontend (built by Vite) at root to serve assets
app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")


@app.on_event("startup")
def startup_event() -> None:
    Base.metadata.create_all(bind=engine)
    apply_seed_if_needed()


@app.get("/")
async def root() -> FileResponse:
    return FileResponse("frontend/dist/index.html")


# Routers
app.include_router(notes_router.router)
app.include_router(action_items_router.router)
app.include_router(tags_router.router)


# Catch-all for SPA routing - serve index.html for unknown paths (must be last)
@app.get("/{path:path}")
async def serve_spa(path: str) -> FileResponse:
    return FileResponse("frontend/dist/index.html")
