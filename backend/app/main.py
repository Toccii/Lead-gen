from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import campaigns, execution_logs, leads, sourcing
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title="Lead-gen API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(campaigns.router)
app.include_router(sourcing.router)
app.include_router(leads.router)
app.include_router(execution_logs.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
