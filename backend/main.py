"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from pathlib import Path
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.database import engine, Base
from backend.models import Image  # noqa: F401 - ensure model is registered
from backend.routers import images, cos_sts, image_gen, templates, cos_serve, prompts, tasks, assets, evolution, chat, config, models as models_router, analytics

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="AI Gallery API",
    description="Backend API for AI-generated image gallery",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: allow frontend origin
allowed_origin = os.environ.get("CORS_ALLOW_ORIGIN", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[allowed_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["content-type"],
)


@app.middleware("http")
async def no_cache_frontend(request, call_next):
    """Force the browser to revalidate frontend assets so code changes show
    up immediately (ETag still yields 304 when unchanged). Fixes the recurring
    "edited but page is stale" problem without manual hard-refresh."""
    response = await call_next(request)
    path = request.url.path
    if request.method in ("GET", "HEAD") and (
        path == "/" or path.endswith((".html", ".js", ".css", ".json"))
    ):
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
    return response


@app.get("/health")
def health():
    return {"ok": True, "backend": "fastapi", "database": "sqlite"}


app.include_router(images.router, prefix="/images", tags=["images"])
app.include_router(cos_sts.router, prefix="/cos", tags=["cos"])
app.include_router(image_gen.router, prefix="/generate", tags=["generate"])
app.include_router(templates.router, prefix="/api", tags=["templates"])
app.include_router(cos_serve.router, tags=["cos-serve"])
app.include_router(prompts.router, prefix="/prompts", tags=["prompts"])
app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(assets.router)
app.include_router(assets.tasks_router)
app.include_router(evolution.router, prefix="/api")
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(config.router, prefix="/api", tags=["config"])
app.include_router(models_router.router, prefix="/api", tags=["models"])
app.include_router(analytics.router, tags=["analytics"])

# Serve locally-persisted generated images at /generated
generated_dir = Path(__file__).resolve().parent.parent / "output" / "generated"
generated_dir.mkdir(parents=True, exist_ok=True)
app.mount("/generated", StaticFiles(directory=str(generated_dir)), name="generated")

# Mount static frontend files
static_dir = Path(__file__).resolve().parent.parent / "public"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="frontend")
