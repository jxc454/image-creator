import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s-%(filename)s-%(levelname)s-%(message)s")
file_handler = logging.FileHandler(f"{__name__}.log")
# file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
# stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(formatter)

# handlers
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
