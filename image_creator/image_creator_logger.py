import logging


def build_logger(level: int):
    logger = logging.getLogger(__name__)
    logger.setLevel(level)

    formatter = logging.Formatter("%(asctime)s-%(filename)s-%(levelname)s-%(message)s")
    file_handler = logging.FileHandler("image-creator.log")
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    # handlers
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    logging.basicConfig(
        handlers=[file_handler, stream_handler],
        level=level,
    )
