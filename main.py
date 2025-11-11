# main.py
import uvicorn
from src import create_app
from src.core.config.config import env
from src.utils.logging_config import build_logging_config

app = create_app(config_name=env.APP_ENV)

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=env.API_PORT,
        lifespan="on",
        log_config=build_logging_config(),  # ← usa el dictConfig dinámico
    )
