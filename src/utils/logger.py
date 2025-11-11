import logging
import sys
from typing import List, Optional
from logging.handlers import TimedRotatingFileHandler
import os

_LOG_FORMAT: str = (
    '%(asctime)s - [%(levelname)s] %(name)s '
    '[%(module)s.%(funcName)s:%(lineno)d]: %(message)s'
)


class MainLogger:
    @classmethod
    def create_console_handler(cls, log_format: str = _LOG_FORMAT) -> logging.Handler:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)
        return handler

    @classmethod
    def create_file_handler(
            cls,
            use_utc: bool = True,
            when: str = 'midnight',
            encoding: str = 'utf-8',
            backup_count: int = 5,
            filename: str = 'logs/app.log',
            log_format: str = _LOG_FORMAT
    ) -> logging.Handler:
        log_dir = os.path.dirname(filename)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        handler = TimedRotatingFileHandler(
            filename=filename,
            when=when,
            encoding=encoding,
            utc=use_utc,
            backupCount=backup_count
        )
        handler.namer = lambda name: name.replace('.log', '') + '.log'
        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)
        return handler

    @classmethod
    def create_default_handlers(cls) -> List[logging.Handler]:
        return [
            cls.create_console_handler(),
            cls.create_file_handler()
        ]

    @classmethod
    def get_logger(
            cls,
            name: str,
            level: int | str = logging.INFO,
            propagate: bool = False,
            handlers: List[logging.Handler] | None = None
    ) -> logging.Logger:
        if handlers is None:
            handlers = cls.create_default_handlers()

        logger = logging.getLogger(name)
        logger.setLevel(level)
        for handler in handlers:
            logger.addHandler(handler)
        logger.propagate = propagate
        return logger
