import logging
import os
from typing import Optional

def _get_formatter() -> logging.Formatter:
    return logging.Formatter(
        "[{asctime}] [{levelname}] {name}: {message}",
        datefmt="%Y/%m/%d %H:%M:%S",
        style="{"
    )

def get_logs_dir() -> str:
    logs_dir = os.path.join(os.path.dirname(__file__), '../../logs')
    os.makedirs(logs_dir, exist_ok=True)

    return logs_dir

def _get_file_handler(log_name: str, log_level: int) -> logging.FileHandler:
    logs_dir = get_logs_dir()

    file_handler = logging.FileHandler(os.path.join(logs_dir, f'{log_name}.log'))
    file_handler.setLevel(log_level)
    file_handler.setFormatter(_get_formatter())

    return file_handler

def _get_console_handler(log_level: int) -> logging.StreamHandler:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(_get_formatter())

    return console_handler

def init_logging(log_name: str, log_level: int, file_log_level: Optional[int] = None) -> logging.Logger:
    logger = logging.getLogger(log_name)
    logger.setLevel(log_level)

    file_handler = _get_file_handler(log_name, file_log_level if file_log_level else log_level)
    console_handler = _get_console_handler(log_level)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger