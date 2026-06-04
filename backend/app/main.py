"""FastAPI app entrypoint for the LBank Futures Position Widget (read-only)."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import lbank_widget
from app.config import get_settings
from app.db.database import init_db


def create_app() -> FastAPI:
    app = FastAPI(
        title="LBank Futures Position Widget (read-only)",
        version="0.1.0",
        description=(
            "Read-only widget backend. Queries + display + risk only. "
            "No trading, no withdrawal."
        ),
    )

    # Local widget preview is a static page; allow it to fetch the API.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # Create tables on app construction so the app is usable immediately
    # (also works under TestClient without a startup-event lifespan).
    init_db()

    @app.get("/healthz")
    def healthz() -> dict:
        # Exposes only the safe settings subset (no key/secret).
        return {"status": "ok", **get_settings().public_dict()}

    app.include_router(lbank_widget.router)
    return app


app = create_app()
