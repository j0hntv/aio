import logging


def setup_logger(logger, level):
    handler = logging.StreamHandler()
    logger.addHandler(handler)
    logger.setLevel(level)
