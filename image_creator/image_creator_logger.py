import logging
import os


class MakeFileHandler(logging.FileHandler):
    def __init__(self, filename, mode="a", encoding=None, delay=0):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        os.makedirs(os.path.join(os.path.dirname(filename), "images"), exist_ok=True)
        logging.FileHandler.__init__(self, filename, mode, encoding, delay)


formatter = logging.Formatter("%(asctime)s-%(filename)s-%(levelname)s-%(message)s")
file_handler = MakeFileHandler("logs/image-creator.log")
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logging.basicConfig(
    handlers=[file_handler, stream_handler], level=logging.INFO,
)

logger = logging.getLogger()
