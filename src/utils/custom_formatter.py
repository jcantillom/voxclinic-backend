import logging
import os
from datetime import datetime, timezone, timedelta
from colorama import Fore, Style

# Colores por nivel
LOG_COLORS = {
    "INFO": Fore.GREEN,
    "ERROR": Fore.RED,
    "WARNING": Fore.YELLOW,
    "DEBUG": Fore.BLUE
}


class CustomFormatter(logging.Formatter):
    def format(self, record):
        colombia_tz = timezone(timedelta(hours=-5))
        record_time = datetime.now(colombia_tz).strftime("%Y-%m-%d %H:%M:%S")

        level_color = LOG_COLORS.get(record.levelname, "")
        level_name = f"{level_color}[{record.levelname}]{Style.RESET_ALL}"

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
        try:
            relative_path = os.path.relpath(record.pathname, start=project_root)
        except Exception:
            relative_path = record.pathname

        file_path = f"[{relative_path}:{record.lineno}]"

        event_filename = getattr(record, "event_filename", None)
        event_filename_str = f"[{event_filename}]" if event_filename else ""

        log_message = f"{record_time} {level_name} {file_path} {event_filename_str} - {record.getMessage()}"
        return log_message
