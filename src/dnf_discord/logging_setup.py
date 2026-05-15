import logging
from datetime import date
from pathlib import Path


def setup_logging(log_dir: Path, level: int = logging.INFO) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"dnf_discord_{date.today().strftime('%Y-%m-%d')}.log"

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    _reset_handlers(root_logger)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    return log_file


def _reset_handlers(logger: logging.Logger) -> None:
    if not logger.handlers:
        return
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
