import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging():
    logger = logging.getLogger('dairy')
    if logger.handlers:
        return

    log_directory = Path(__file__).resolve().parents[1] / 'logs'
    log_directory.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter('%(levelname)s %(module)s %(message)s')
    console_handler = logging.StreamHandler()
    file_handler = RotatingFileHandler(
        log_directory / 'app.log',
        maxBytes=5_000_000,
        backupCount=3,
        encoding='utf-8',
    )
    for handler in (console_handler, file_handler):
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.WARNING)
    logger.propagate = False


def get_logger(module_name):
    return logging.getLogger(f'dairy.{module_name}')
