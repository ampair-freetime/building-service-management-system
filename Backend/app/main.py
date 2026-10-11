import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings


def _configure_app_logging() -> None:
    """Show INFO logs from app.* modules; Uvicorn only configures its own loggers.

    Without a handler Python prints WARNING and above only, so successful email
    deliveries and other logger.info() events were invisible.
    """
    logger = logging.getLogger("app")
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s:     %(name)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def create_application() -> FastAPI:
    _configure_app_logging()
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_router, prefix=settings.api_v1_prefix)

    @application.get("/health", include_in_schema=False)
    async def health() -> dict[str, str]:
        """Liveness only: this does not verify database, SMTP or R2 readiness."""
        return {"status": "ok"}

    return application


app = create_application()
