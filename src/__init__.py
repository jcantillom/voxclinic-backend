# src/__init__.py
from fastapi import FastAPI, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from starlette_context import plugins
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette_context.middleware import RawContextMiddleware
from pydantic import ValidationError
import asyncio
import logging
import time

from src.core.config.app_config import config_by_name
from src.core.connections.database import DataAccessLayer

# -------------------------------------------------------------------
#                         Rutas de dominio
# -------------------------------------------------------------------
from src.apps.tenant.controller import router as tenant_router
from src.apps.users.controller import router as user_router
from src.apps.auth.controller import router as auth_router
from src.apps.recordings.controllers.recording_controller import router as recording_router
from src.apps.storage.controller import router as storage_router
from src.apps.recordings.controllers.webhook_controller import router as webhook_router
from src.apps.onboarding.controller import router as onboarding_router
from src.apps.dashboard.controller import router as dashboard_router
from src.apps.document.controllers import router as document_controller
from src.apps.patients.controller import router as patient_controller
from src.apps.schedule.controller import router as schedule_controller

# -------------------------------------------------------------------
log = logging.getLogger("app")


# -------------------------------------------------------------------
# Lifecycle
# -------------------------------------------------------------------
async def on_startup(app: FastAPI) -> None:
    """Crear tablas al iniciar."""
    dal = app.state.db
    dal.create_tables()
    log.info("DB tables ensured.")


async def on_shutdown(app: FastAPI) -> None:
    """Cerrar conexiones al apagar."""
    dal = app.state.db
    dal.close_session()
    log.info("DB session closed.")


# -------------------------------------------------------------------
# Middleware solo-DEBUG para ver body y tiempos
# -------------------------------------------------------------------
from starlette.middleware.base import BaseHTTPMiddleware


class DebugRequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if log.isEnabledFor(logging.DEBUG):
            try:
                raw = await request.body()
                preview = raw.decode() if raw else "<empty>"
            except Exception:
                preview = "<unreadable>"
            log.debug("REQ %s %s body=%s", request.method, request.url.path, preview)

        start = time.time()
        response = await call_next(request)
        dur_ms = (time.time() - start) * 1000

        if log.isEnabledFor(logging.DEBUG):
            log.debug(
                "RES %s %s status=%s time=%.2fms",
                request.method, request.url.path, response.status_code, dur_ms
            )
        return response


# -------------------------------------------------------------------
# Factory
# -------------------------------------------------------------------
def create_app(config_name: str) -> FastAPI:
    """
    Crea la app FastAPI con la config indicada.
    """
    # Contexto por request (request_id, correlation_id)
    ctx_middleware = Middleware(
        RawContextMiddleware,
        plugins=(
            plugins.CorrelationIdPlugin(),
            plugins.RequestIdPlugin(),
        ),
    )

    cfg = config_by_name[config_name]

    app = FastAPI(
        **cfg.dict(),  # title, description, version, debug, etc.
        middleware=[ctx_middleware],
        on_startup=[lambda: asyncio.create_task(on_startup(app))],
        on_shutdown=[lambda: asyncio.create_task(on_shutdown(app))],
    )

    # DB
    app.state.db = DataAccessLayer()

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Total-Count"],
    )

    # Debug request/response (solo si LOG_LEVEL=DEBUG)
    app.add_middleware(DebugRequestLogMiddleware)

    # -------------------------------------------------------------------
    # Exception Handlers: muestran la causa real en consola
    # -------------------------------------------------------------------
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        log.warning(
            "HTTPException %s %s -> %s | detail=%s",
            request.method, request.url.path, exc.status_code, exc.detail
        )
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        log.warning(
            "ValidationError %s %s -> 422 | errors=%s",
            request.method, request.url.path, exc.errors()
        )
        return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            content={"detail": exc.errors()})

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # imprime traceback completo
        log.exception("Unhandled %s %s -> 500", request.method, request.url.path)
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content={"detail": "Internal Server Error"})

    # -------------------------------------------------------------------
    # Rutas base
    # -------------------------------------------------------------------
    @app.get("/")
    async def root():
        return {"message": "🚀 Server is running"}

    # -------------------------------------------------------------------
    #                          Rutas de dominio
    # -------------------------------------------------------------------
    app.include_router(
        tenant_router,
        prefix="/api/v1",
        tags=["Tenants"],
    )

    app.include_router(
        user_router,
        prefix="/api/v1",
        tags=["Users"],
    )

    app.include_router(
        auth_router,
        prefix="/api/v1",
        tags=["Auth"],
    )

    app.include_router(
        recording_router,
        prefix="/api/v1",
        tags=["Recordings"],
    )

    app.include_router(
        storage_router,
        prefix="/api/v1",
        tags=["Storage"],
    )

    app.include_router(
        webhook_router,
        prefix="/api/v1",
        tags=["Webhooks"],
    )

    app.include_router(
        onboarding_router,
        prefix="/api/v1",
        tags=["Onboarding"],
    )

    app.include_router(
        dashboard_router,
        prefix="/api/v1",
        tags=["Dashboard"],
    )

    app.include_router(
        document_controller,
        prefix="/api/v1",
        tags=["Documents"],
    )

    app.include_router(
        patient_controller,
        prefix="/api/v1",
        tags=["Patients"],
    )

    app.include_router(
        schedule_controller,
        prefix="/api/v1",
        tags=["Schedule"],
    )

    return app
