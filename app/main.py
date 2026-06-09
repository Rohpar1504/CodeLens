from fastapi import FastAPI
from app.webhooks.routes import router as webhooks_router

app = FastAPI(
    title="CodeLens",
    description="AI-powered code review platform",
    version="0.1.0",
)

# Routers
app.include_router(webhooks_router, prefix="/github", tags=["github"])

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "codelens"}