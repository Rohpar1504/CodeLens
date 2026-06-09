from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.webhooks.routes import router as webhooks_router
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    print("[app] Database initialized")
    yield


app = FastAPI(
    title="CodeLens",
    description="AI-powered code review platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(webhooks_router, prefix="/github", tags=["github"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "codelens"}