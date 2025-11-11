import uvicorn
from src import create_app
from src.core.config.config import env
from src.utils.logger import MainLogger

# Crea la aplicación de FastAPI, con el entorno de configuración.
app = create_app(config_name=env.APP_ENV)


async def startup_event():
    """
    Esta función se ejecuta al iniciar el servidor de uvicorn,
    Crea un logger para el servidor de uvicorn
    """

    file_handler = MainLogger.create_file_handler(
        filename='logs/uvicorn.log'
    )
    MainLogger.get_logger(
        name='uvicorn',
        propagate=True,
        handlers=[file_handler]
    )


# Registra el evento de inicio de la aplicación.
app.add_event_handler("startup", startup_event)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=env.API_PORT,
        lifespan='on',
    )
