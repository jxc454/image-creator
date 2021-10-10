import datetime

try:
    # this import structure is to un-confuse pycharm
    from cv2 import cv2 as cv
except ImportError:
    print("NO CV2")
import typer
import yaml
import picamera
import os
from picamera.array import PiRGBArray
import time

app = typer.Typer()

# with open("config/production.yaml", "r") as stream:
#     config = yaml.safe_load(stream)

# default width/height = 3840x2160


# constants
BLUR_SIZE = (5, 5)
GRAY_THRESHOLD = 15
MIN_AREA = 4096


@app.command()
def start():
    # write_to = config.files.image.saveDir
    write_to = "/home/pi/Desktop/images"
    # frequency = config.camera.imagesPerSecond

    with picamera.PiCamera(
        camera_num=0, sensor_mode=0, clock_mode="reset", resolution=[1280, 960]
    ) as camera:
        # let the camera "warm up"
        time.sleep(0.9)

        camera.vflip = True

        raw_capture = PiRGBArray(camera, size=camera.resolution)
        base_image = None

        i = 0
        for frame in camera.capture_continuous(
            raw_capture, format="bgr", use_video_port=True
        ):
            # initialize the timestamp
            timestamp = datetime.datetime.now()
            print(str(i), str(timestamp))

            # grab the raw NumPy array representing the image
            image = frame.array

            # convert the image to grayscale, and blur it
            gray = cv.GaussianBlur(cv.cvtColor(image, cv.COLOR_BGR2GRAY), BLUR_SIZE, 0)

            # if the base image has not been defined, initialize it
            if base_image is None:
                base_image = gray.copy()
                cv.imwrite(
                    os.path.join("/home/pi/Desktop/images", "0base-image" + ".jpg"),
                    base_image,
                )
                print("saved base image!!")

                lastTime = timestamp
                raw_capture.truncate(0)
                i += 1
                continue

            # compute the absolute difference between the current image and
            # base image and then turn everything lighter gray than THRESHOLD into white
            frame_delta = cv.absdiff(gray, base_image)
            threshold_image = cv.threshold(
                frame_delta, GRAY_THRESHOLD, 255, cv.THRESH_BINARY
            )[1]

            # dilate the threshold_image to fill in any holes, then find contours
            threshold_image = cv.dilate(threshold_image, None, iterations=2)
            (contours, _) = cv.findContours(
                threshold_image.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE
            )

            raw_capture.truncate(0)

            # look for motion
            motion_found = False
            biggest_area = 0

            # examine the contours, looking for the largest one
            x = None
            for c in contours:
                (x1, y1, w1, h1) = cv.boundingRect(c)
                found_area = w1 * h1

                if (
                    (found_area > MIN_AREA)
                    and (found_area > biggest_area)
                    and biggest_area != 1280 * 960
                ):
                    biggest_area = found_area
                    # motion_found = True
                    x = x1
                    y = y1
                    h = h1
                    w = w1

            # if we found a qualifying delta then draw a rect
            if x is not None:
                cv.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 5)

            write_to = "/home/pi/Desktop/images"
            save_to = os.path.join(write_to, str(i) + ".jpg")
            save_to_2 = os.path.join(write_to, str(i) + "b.jpg")
            cv.imwrite(save_to, image)
            cv.imwrite(save_to_2, threshold_image)

            i += 1
            if i > 10:
                break

        print("Done")


def image_creator():
    app()
