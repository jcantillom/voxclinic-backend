from pydantic_settings import BaseSettings
from typing import Dict


class Config(BaseSettings):
    """Configuracion base de la aplicacion."""

    debug: bool = False
    description: str = "Invox - medical invoicing system"
    contact: Dict[str, str] = {
        "name": "Juan Cantillo",
        "email": "jjcantillo7230@gmail.com"
    }


class DevelopmentConfig(Config):
    """
    Configuracion de desarrollo.
    """
    debug: bool = True
    title: str = "Api Invox - Development"
    version: str = "v1.0"
    description: str = "Api Ms_analytics - Development"


class ProductionConfig(Config):
    """Configuracion de produccion."""

    title: str = "Api Invox"
    version: str = "v1.0"
    description: str = ""


class TestingConfig(Config):
    """Configuracion de pruebas."""

    title: str = "Api Invox - Testing"
    version: str = "v1.0"
    description: str = ""
    debug: bool = True
    testing: bool = True


# Configuracion de la aplicacion, dependiendo del entorno.
config_by_name = {
    "development": DevelopmentConfig(),
    "production": ProductionConfig(),
    "testing": TestingConfig(),
}
