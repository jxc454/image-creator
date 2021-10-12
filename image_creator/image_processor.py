import datetime
import logging
import math
import os

from image_creator.config.image_creator_config import ImageCreatorConfig
from dataclasses import dataclass, astuple

try:
    # this import structure is to un-confuse pycharm
    from cv2 import cv2 as cv
except ImportError:
    pass

logger = logging.getLogger(__name__)
image_log_dir = os.path.join(
    os.path.dirname(logger.root.handlers[0].baseFilename), "images"
)


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
    def __init__(self, config: ImageCreatorConfig):
        # state
        self.base_image = None
        self.base_timestamp = None

        self.key = None
        self.positions = []
        self.top_speed = -math.inf
        self.mph_image = None
        self.mph_image_time = None

        self.image = None
        self.image_time = None

        # config
        self.base_image_ttl = config.base_image_ttl
        self.max_time_delta = config.max_time_delta
        self.save_dir = config.image_save_dir
        self.ft_to_target = config.ft_to_target
        self.field_of_view = config.field_of_view
        self.image_buffer = config.image_buffer
        self.width = config.width
        self.height = config.height
        self.min_area = config.min_area
        self.min_speed = config.min_speed
        self.max_speed = config.max_speed

        # constants
        self.blur_size = (15, 15)
        self.gray_threshold = 15

    def tracking(self):
        return len(self.positions) > 0

    def mph(self, pixels_per_ms):
        miles_per_pixel = (
            2
            * (math.tan(math.radians(self.field_of_view / 2)) * self.ft_to_target)
            / self.width
            / 5280
        )

        return pixels_per_ms * 3600e3 * miles_per_pixel

    def place_image(self, image, capture_time):
        """
        if there's no image, then the input becomes the base_image
        if there's an image, but we're not tracking and the image's time is up, then the input becomes the base image
        Otherwise just set self.image to the input
        """
        # TODO - try to apply this logic only after we "know" that the image doesn't have motion
        if self.base_image is None or (
            self.base_timestamp + self.base_image_ttl < capture_time
            and not self.tracking()
        ):
            # we're not tracking anything, and the base_image's time is up
            self.base_image = cv.GaussianBlur(
                cv.cvtColor(image, cv.COLOR_BGR2GRAY), self.blur_size, 0
            )
            self.base_timestamp = capture_time
            logger.info("Replacing base_image")

            if logger.level <= logging.DEBUG:
                base_image_path = os.path.join(image_log_dir, "base_image.jpg")
                logger.debug("writing new base_image to %s" % base_image_path)
                cv.imwrite(base_image_path, image)
        else:
            # this image should be processed
            self.image = image
            self.image_time = capture_time
            logger.debug("Setting new image")

        return self

    def detect_motion(self):
        # if there is a key, clear it if we've been going for too long
        if self.key is not None and self.image_time > self.key + self.max_time_delta:
            logger.info(
                "Clearing session %d (with %d positions) because it timed out"
                % (self.key, len(self.positions))
            )
            self.positions.clear()
            self.key = None
            self.mph_image = None
            self.mph_image_time = None
            # TODO should probably reset the base_image here, because the continous motion detection might be
            #  an issue with comparison to the base_image

        # if there is no image, do nothing
        if self.image is None:
            logger.debug("No image, not detecting motion")
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

        # dilate the threshold_image then find contours
        threshold_image = cv.dilate(threshold_image, None, iterations=2)
        (contours, _) = cv.findContours(
            threshold_image.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE
        )

        # look for motion
        greatest_area = 0

        # examine the contours, looking for the largest one
        position = Position(None, None, self.image_time)
        for c in contours:
            (x, y1, width, height) = cv.boundingRect(c)
            found_area = width * height

            if (
                (found_area > self.min_area)
                and (found_area > greatest_area)
                and greatest_area != self.width * self.height
            ):
                greatest_area = found_area
                position.x_left = x
                position.x_right = x + width

        if position.x_left is not None:
            if self.key is None:
                self.key = self.image_time
                logger.info(
                    "Found new motion!  key=%f left=%s, right=%s, timestamp=%f"
                    % (self.key, position.x_left, position.x_right, position.timestamp)
                )
            else:
                logger.info(
                    "Adding motion to existing key=%f left=%s, right=%s, timestamp=%f"
                    % (self.key, position.x_left, position.x_right, position.timestamp)
                )

            if logger.level <= logging.DEBUG:
                threshold_image_path = os.path.join(
                    image_log_dir, f"threshold_image_{self.key}_{self.image_time}.jpg"
                )
                logger.debug("writing new threshold_image to %s" % threshold_image_path)
                cv.imwrite(threshold_image_path, threshold_image)

            self.positions.append(position)
        else:
            # no motion
            logger.debug("No motion found")
            # if this is the end of some motion then write the image
            if self.mph_image is not None:
                mph_dir = os.path.join(
                    self.save_dir,
                    f"max-speed_{round(self.top_speed)}_timestamp_{round(self.mph_image_time // 1e3)}.jpg",
                )

                cv.putText(
                    img=self.mph_image,
                    text=f"{round(self.top_speed)} MPH, {datetime.datetime.fromtimestamp(self.mph_image_time // 1e3)}",
                    org=(self.width // 12, self.height // 12),
                    fontFace=cv.FONT_HERSHEY_SIMPLEX,
                    fontScale=2,
                    thickness=4,
                    lineType=8,
                    color=(0, 0, 255),
                )

                logger.info(
                    "Writing image! key=%f top_speed=%d filename=%s"
                    % (self.key, round(self.top_speed), mph_dir)
                )

                cv.imwrite(
                    mph_dir, self.mph_image,
                )

                self.mph_image = None
                self.mph_image_time = None
                self.key = None

            self.positions.clear()
            self.top_speed = -math.inf

        return self

    def calculate_speed(self):
        if len(self.positions) > 1:
            x_left_last, x_right_last, timestamp_last = self.positions[-1][
                "x_left", "x_right", "timestamp"
            ]
            x_left_prev, x_right_prev, timestamp_prev = self.positions[-2][
                "x_left", "x_right", "timestamp"
            ]

            min_valid = self.image_buffer
            max_valid = self.width - self.image_buffer

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

            logger.info("speed=%d, top_speed=%s" % (speed, str(self.top_speed)))
            if speed > self.top_speed and (self.min_speed <= speed <= self.max_speed):
                self.top_speed = speed

                # update self.image with the mph and timestamp in an overlay
                # put the image in the mph_image slot
                self.mph_image = self.image
                self.mph_image_time = self.image_time

        return self
