import datetime
import math
import os
import time

try:
    # this import structure is to un-confuse pycharm
    from cv2 import cv2 as cv
except ImportError:
    pass


class ImageProcessor:
    def __init__(self):
        self.base_image = None
        self.base_timestamp = None
        self.positions = []
        self.max_speed = -math.inf
        self.image = None
        self.image_time = None
        self.processed_image = None
        self.mph_image = None
        self.key = None

        # config
        self.base_image_ttl = 300000  # 5 minutes
        self.max_time_delta = 5000  # 5 seconds
        self.save_dir = "/home/pi/Desktop/images"

    def tracking(self):
        return len(self.positions) > 0

    def moving_left(self):
        (last_x, _) = self.positions[-1]
        (prev_x, _) = self.positions[-2]

        return last_x - prev_x < 0

    def place_image(self, image, capture_time):
        """
        if there's no image, then the input becomes the base_image
        if there's an image, but we're not tracking and the image's time is up, then the input becomes the base image
        Otherwise just set self.image to the input
        """
        if self.base_image is None or (
            self.base_timestamp + self.base_image_ttl < capture_time
            and not self.tracking()
        ):
            # we're not tracking anything, and the base_image's time is up
            self.base_image = image
            self.base_timestamp = capture_time
        else:
            # this image should be processed
            self.image = image
            self.image_time = capture_time

        return self

    def detect_motion(self):
        # if there is a key, clear it if we've been going for too long
        if self.key is not None and self.image_time > self.key + self.max_time_delta:
            self.positions.clear()

        if self.image is not None:
            # do transforms and set processed_image
            self.processed_image = self.image

            found_motion = False
            x = -1
            if found_motion and x > 5:
                self.positions.append((x, self.image_time))
            else:
                # no motion, or the bounding rect is off the left of the image
                if self.mph_image is not None:
                    cv.imwrite(
                        self.mph_image,
                        os.path.join(
                            self.save_dir,
                            str(self.key) + "_" + str(self.max_speed) + ".jpg",
                        ),
                    )

        return self

    def calculate_speed(self):
        if len(self.positions) > 1:

            (last_x, last_time) = self.positions[-1]
            (prev_x, prev_time) = self.positions[-2]

            speed = (last_x - prev_x) / (last_time - prev_time)

            if speed > self.max_speed:
                self.max_speed = speed
                # update self.image with the mph and timestamp in an overlay
                # put the image in the processed_image slot
                self.mph_image = self.image

        return self
