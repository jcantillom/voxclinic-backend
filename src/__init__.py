from fastapi import FastAPI, Depends, HTTPException
from starlette_context import plugins
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette_context.middleware import RawContextMiddleware
from src.core.config.app_config import config_by_name, Config
from src.core.connections.database import DataAccessLayer
import asyncio
from src.core.errors.http_error_handler import HTTPErrorHandler

from src.apps.tenant.controller import router as tenant_router


async def on_startup(app: FastAPI) -> None:
    """
    Esta función se llama cuando la aplicación inicia,
    se encarga de crear las tablas en la base de datos.
    """
    dal = app.state.db
    dal.create_tables()


async def on_shutdown(app: FastAPI) -> None:
    """
    Esta función se llama cuando la aplicación se detiene,
    se encarga de cerrar la conexión con la base de datos.
    """
    dal = app.state.db
    dal.close_session()


def create_app(config_name: str) -> FastAPI:
    """
    Esta función crea la aplicación FastAPI con la configuración especificada.
    :param config_name: Nombre de la configuración a utilizar.
    :return: Instancia de la aplicación FastAPI.
    """

    ctx_middleware = Middleware(
        RawContextMiddleware,
        plugins=(
            plugins.CorrelationIdPlugin(),
            plugins.RequestIdPlugin()
        )
    )

    # Crea una instancia de la configuración especificada
    config_instance = config_by_name[config_name]

    app = FastAPI(
        **config_instance.dict(),
        middleware=[
            ctx_middleware,
        ],
        on_startup=[lambda: asyncio.create_task(on_startup(app))],
        on_shutdown=[lambda: asyncio.create_task(on_shutdown(app))]
    )
    # Inicializa la conexión con la base de datos
    app.state.db = DataAccessLayer()

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root():
        """
        Ruta inicial de la aplicación.
        """
        return {
            "message": "🚀 Server is running"
        }

    # Add routes
    app.include_router(
        tenant_router,
        prefix="/api/v1",
        tags=["Tenants"],
    )

    return app
