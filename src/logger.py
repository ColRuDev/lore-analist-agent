import logging
import sys


def get_logger(module_name: str) -> logging.Logger:
    """
    Standard logger setup for any module in the project.

    Args:
        module_name (str): Name of the module requesting the logger (usually __name__).

    Returns:
        logging.Logger: Logger instance configured for the module.
    """
    logger = logging.getLogger(module_name)

    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        formato = logging.Formatter(
            fmt="[%(asctime)s] [%(name)s] %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(formato)
        logger.addHandler(console_handler)

    return logger
