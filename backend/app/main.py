from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.deps import get_current_user
from app.api.routers import (
    auth,
    campaigns,
    emails,
    execution_logs,
    jobs,
    leads,
    metrics,
    sourcing,
    system_settings,
    unsubscribe,
)
from app.core.config import get_settings
from app.db.seed import ensure_admin_user
from app.db.session import SessionLocal

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    db = SessionLocal()
    try:
        ensure_admin_user(db)
    except Exception as exc:  # noqa: BLE001 - don't crash startup if the DB isn't migrated yet
        print(f"Warning: could not ensure admin user on startup: {exc}")
    finally:
        db.close()
    yield


app = FastAPI(title="Lead-gen API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.environment == "development" else [settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_protected = [Depends(get_current_user)]

app.include_router(auth.router)
app.include_router(campaigns.router, dependencies=_protected)
app.include_router(sourcing.router, dependencies=_protected)
app.include_router(leads.router, dependencies=_protected)
app.include_router(emails.router, dependencies=_protected)
app.include_router(execution_logs.router, dependencies=_protected)
app.include_router(jobs.router, dependencies=_protected)
app.include_router(metrics.router, dependencies=_protected)
app.include_router(system_settings.router, dependencies=_protected)
app.include_router(unsubscribe.router)  # public: recipients click this link unauthenticated


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
