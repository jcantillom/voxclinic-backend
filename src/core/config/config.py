import os
from pydantic_settings import BaseSettings


class Environment(BaseSettings):
    """
    Environment variables, this class is used to load the environment variables,
    the variables are loaded from the .env file, validate, tha the variables that
    are in the .env file are the same as those that are in the class.
    """
    APP_ENV: str
    DB_HOST: str
    DB_PORT: str
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_DATABASE: str
    ALEMBIC_DATABASE_URL: str


    class Config:
        env_file = os.path.join(os.getcwd(), ".env")
        env_file_encoding = "utf-8"


env: Environment = Environment()
