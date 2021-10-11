from image_creator.image_processor import ImageProcessor
import image_creator.config

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

# default width/height = 3840x2160

app = typer.Typer()

source = files(image_creator.config).joinpath("default.yaml")
with as_file(source) as default_config:
    with open(default_config, "r") as stream:
        config = yaml.safe_load(stream)
        print(config)


@app.command()
def start():
    # write_to = config.files.image.saveDir
    write_to = "/home/pi/Desktop/images"
    # frequency = config.camera.imagesPerSecond

    with picamera.PiCamera(
        camera_num=0, sensor_mode=0, clock_mode="reset", resolution=[1280, 960]
    ) as camera:
        # let the camera "warm up"
        time.sleep(1)
        camera.vflip = True

        processor = ImageProcessor()

        raw_capture = PiRGBArray(camera, size=camera.resolution)
        i = 0
        for frame in camera.capture_continuous(
            raw_capture, format="bgr", use_video_port=True
        ):
            if i == 0:
                # the very first image looks a little different
                raw_capture.truncate(0)
                i += 1
                continue

            print(
                f"{i}, base is None: {processor.base_image is None} image is None: {processor.image is None}"
            )

            # grab the raw NumPy array representing the image
            image = frame.array

            processor.place_image(
                image, time.time() * 1000
            ).detect_motion().calculate_speed()

            raw_capture.truncate(0)

            i += 1

            if i > 10:
                break

    print("Done")


def image_creator():
    app()
