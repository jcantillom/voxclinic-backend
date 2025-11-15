import os


def build_logging_config():
    """
    Devuelve un dictConfig para Uvicorn/FastAPI:
      - Solo consola (sin archivos .log)
      - Formato limpio y breve
      - Colores opcionales con LOG_COLOR=1 (requiere 'colorlog')
      - Nivel controlado con LOG_LEVEL (DEBUG/INFO/WARNING/ERROR)
    """
    # CAMBIO: Usamos 'DEBUG' si no está definido para facilitar la depuración
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()
    USE_COLOR = os.getenv("LOG_COLOR", "0") == "1"

    BASE_FORMAT = "[%(levelname)s] [%(asctime)s] [%(filename)s:%(lineno)d] %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    # Formatter común o coloreado
    if USE_COLOR:
        # Necesita: pip install colorlog
        default_formatter = {
            "()": "colorlog.ColoredFormatter",
            "format": "%(log_color)s" + BASE_FORMAT,
            "datefmt": DATE_FORMAT,
            "log_colors": {
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        }
    else:
        default_formatter = {
            "format": BASE_FORMAT,
            "datefmt": DATE_FORMAT,
        }

    return {
        "version": 1,
        "disable_existing_loggers": False,

        "formatters": {
            "default": default_formatter,
        },

        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",  # ← importante: ext:// para dictConfig
                "level": LOG_LEVEL,
                "formatter": "default",
            }
        },

        # Loggers: root + uvicorn
        "loggers": {
            # Root (tu app)
            "": {
                "handlers": ["console"],
                "level": LOG_LEVEL,  # <-- Usa el nivel DEBUG/INFO/etc
                "propagate": False,
            },

            # Uvicorn: error + access
            "uvicorn": {
                "handlers": ["console"],
                "level": LOG_LEVEL,  # <-- Usa el nivel DEBUG/INFO/etc
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["console"],
                "level": LOG_LEVEL,  # <-- Usa el nivel DEBUG/INFO/etc
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": LOG_LEVEL,  # <-- Usa el nivel DEBUG/INFO/etc
                "propagate": False,
            },
        },
    }
