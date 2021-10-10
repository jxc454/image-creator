import math
import os

try:
    # this import structure is to un-confuse pycharm
    from cv2 import cv2 as cv
except ImportError:
    pass

from dataclasses import dataclass, astuple


@dataclass
class Position:
    x_left = None
    x_right = None
    timestamp = None

    def __init__(self, x_left=None, x_right=None, timestamp=None):
        self.x_left = x_left
        self.x_right = x_right
        self.timestamp = timestamp

    def __iter__(self):
        return iter(astuple(self))

    def __getitem__(self, keys):
        return iter(getattr(self, k) for k in keys)


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
        self.ft_to_target = 50
        self.field_of_view = 53.5

        # constants
        self.blur_size = (15, 15)
        self.gray_threshold = 15
        self.min_area = 16384
        self.width = 1280
        self.height = 960

    def tracking(self):
        return len(self.positions) > 0

    def mph(self, pixels_per_ms):
        miles_per_pixel = (
            2
            * (math.tan(math.radians(self.field_of_view / 2)) * self.ft_to_target)
            / self.width
            / 5280
        )

        return pixels_per_ms * 3600000 * miles_per_pixel

    def place_image(self, image, capture_time):
        """
        if there's no image, then the input becomes the base_image
        if there's an image, but we're not tracking and the image's time is up, then the input becomes the base image
        Otherwise just set self.image to the input
        """
        if len(self.positions) > 0:
            # TODO - debug logging
            for p in self.positions:
                print(f"{p.x_left}, {p.x_right}, {p.timestamp}")

        if self.base_image is None or (
            self.base_timestamp + self.base_image_ttl < capture_time
            and not self.tracking()
        ):
            # we're not tracking anything, and the base_image's time is up
            self.base_image = cv.GaussianBlur(
                cv.cvtColor(image, cv.COLOR_BGR2GRAY), self.blur_size, 0
            )
            self.base_timestamp = capture_time

            cv.imwrite(os.path.join(self.save_dir, "base_image.jpg"), image)
        else:
            # this image should be processed
            self.image = image
            self.image_time = capture_time

        return self

    def detect_motion(self):
        # if there is a key, clear it if we've been going for too long
        if self.key is not None and self.image_time > self.key + self.max_time_delta:
            self.positions.clear()
            self.key = None

        # if there is no image, do nothing
        if self.image is None:
            return self

        # convert the image to grayscale, and blur it
        gray = cv.GaussianBlur(
            cv.cvtColor(self.image, cv.COLOR_BGR2GRAY), self.blur_size, 0
        )

        # compute the absolute difference between the current image and
        # base image and then turn everything lighter gray than THRESHOLD into white
        frame_delta = cv.absdiff(gray, self.base_image)
        threshold_image = cv.threshold(
            frame_delta, self.gray_threshold, 255, cv.THRESH_BINARY
        )[1]

        # dilate the threshold_image to fill in any holes, then find contours
        threshold_image = cv.dilate(threshold_image, None, iterations=2)
        (contours, _) = cv.findContours(
            threshold_image.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE
        )

        # look for motion
        biggest_area = 0

        # examine the contours, looking for the largest one
        position = Position(None, None, self.image_time)
        y = 0
        height = 0
        for c in contours:
            (x, y1, width, height) = cv.boundingRect(c)
            found_area = width * height

            if (
                (found_area > self.min_area)
                and (found_area > biggest_area)
                and biggest_area != self.width * self.height
            ):
                print(f"found area - {found_area}")
                biggest_area = found_area
                position.x_left = x
                position.x_right = x + width

                y = y1

        self.processed_image = self.image

        if position.x_left is not None:
            if self.key is None:
                self.key = self.image_time

            self.positions.append(position)
            cv.rectangle(
                self.image,
                (position.x_left, y),
                (position.x_right, y + height),
                (0, 255, 0),
                5,
            )

            # TODO - debug logging
            cv.imwrite(
                os.path.join(
                    self.save_dir, f"threshold-{self.image_time}-{position.x_left}.jpg"
                ),
                threshold_image,
            )
        else:
            # no motion
            # is this the end of some piece of motion?
            if self.mph_image is not None:
                cv.imwrite(
                    os.path.join(self.save_dir, f"max-speed-{self.max_speed}.jpg",),
                    self.mph_image,
                )

                self.positions.clear()

        return self

    def calculate_speed(self):
        if len(self.positions) > 1:
            x_left_last, x_right_last, timestamp_last = self.positions[-1][
                "x_left", "x_right", "timestamp"
            ]
            x_left_prev, x_right_prev, timestamp_prev = self.positions[-2][
                "x_left", "x_right", "timestamp"
            ]

            min_valid = 4
            max_valid = self.width - 4

            # if each left value is not cut-off then use the left values, else try the right values
            # else, we can't know the distance (without already knowing the length of the moving object)
            distance = (
                (x_right_last - x_right_prev)
                if min_valid < x_right_last < max_valid
                and min_valid < x_right_prev < max_valid
                else (x_left_last - x_left_prev)
                if min_valid < x_left_last < max_valid
                and min_valid < x_left_prev < max_valid
                else None
            )

            # TODO - left-to-right movement will be closer to camera than
            #  right-to-left movement
            speed = self.mph(
                abs(distance / (timestamp_last - timestamp_prev))
                if distance is not None
                else -math.inf
            )

            if speed > self.max_speed:
                self.max_speed = speed

                # update self.image with the mph and timestamp in an overlay
                # put the image in the mph_image slot
                self.mph_image = self.image

        return self
