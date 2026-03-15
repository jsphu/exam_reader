import logging
import sys

def setup_logger():
    """
    Sets up a logger that only displays messages if verbose is True.
    """
    logger = logging.getLogger("exam_reader")
    logger.propagate = False
    # Remove existing handlers to avoid duplicates
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
