from image_creator.image_processor import ImageProcessor
import image_creator.config
from image_creator.config.image_creator_config import ImageCreatorConfig
import dacite
import pprint

try:
    # this import structure is to un-confuse pycharm
    from cv2 import cv2 as cv
except ImportError:
    print("NO CV2")
import typer
import yaml
import picamera
from picamera.array import PiRGBArray
import time
from importlib_resources import files, as_file
from image_creator.image_creator_logger import logger

# default width/height = 3840x2160

app = typer.Typer()

# load default config
source = files(image_creator.config).joinpath("default.yaml")
with as_file(source) as default_config:
    with open(default_config, "r") as stream:
        default_config_dict = yaml.safe_load(stream)


@app.command()
def start(config_path=None):
    # overlay config input on default config
    if config_path is not None:
        with open(config_path, "r") as user_config_stream:
            merged_config_dict = {
                **default_config_dict,
                **yaml.safe_load(user_config_stream),
            }
            config = dacite.from_dict(ImageCreatorConfig, merged_config_dict)

    logger.info("Starting up with config: %s" % (pprint.pformat(merged_config_dict)))

    with picamera.PiCamera(
        camera_num=0,
        sensor_mode=0,
        clock_mode="reset",
        resolution=[config.width, config.height],
    ) as camera:
        # let the camera "warm up"
        time.sleep(1)
        camera.vflip = True

        processor = ImageProcessor(config)

        raw_capture = PiRGBArray(camera, size=camera.resolution)
        i = 0
        for frame in camera.capture_continuous(
            raw_capture, format="bgr", use_video_port=True
        ):
            # the very first image always looks a little strange, even with the warm-up, so skip it
            if i != 0:
                # grab the raw NumPy array representing the image
                image = frame.array

                processor.place_image(
                    image, time.time() * 1000
                ).detect_motion().calculate_speed()

            raw_capture.truncate(0)
            i += 1

            if i > 100:
                break


def image_creator():
    app()
