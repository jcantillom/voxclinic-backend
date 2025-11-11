import os
from typing import Iterator
from contextlib import contextmanager

from sqlalchemy.engine import URL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from dotenv import load_dotenv

Base = declarative_base()
load_dotenv()


class DataAccessLayer:
    """Administra engine y session factory."""

    def __init__(self):
        sql_database_url: URL = URL.create(
            'postgresql+psycopg2',
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            username=os.getenv("DB_USERNAME"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_DATABASE"),
        )

        self.engine = create_engine(
            sql_database_url,
            pool_pre_ping=True,
            pool_size=30,
            max_overflow=20,
        )

        self.session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            expire_on_commit=False,
        )

    @contextmanager
    def session_scope(self) -> Iterator[Session]:
        db = self.session_factory()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def create_tables(self) -> None:
        Base.metadata.create_all(self.engine)

    def close_session(self) -> None:
        try:
            self.engine.dispose(close=True)
        except Exception:
            pass
