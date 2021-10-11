import dataclasses
import math
import pytest

from image_creator.config.image_creator_config import ImageCreatorConfig
from image_creator.image_processor import ImageProcessor, Position

WIDTH = 1200

BASE_CONFIG = ImageCreatorConfig(
    width=0,
    height=0,
    x_min=0,
    x_max=0,
    y_min=0,
    y_max=0,
    base_image_ttl=0,
    max_time_delta=0,
    min_area=0,
    ft_to_target=0,
    field_of_view=0.0,
    image_buffer=0,
    image_save_dir="",
    metadata_save_dir="",
)


@pytest.fixture
def empty_processor():
    config = dataclasses.replace(BASE_CONFIG)
    config.width = WIDTH
    config.field_of_view = 90
    config.ft_to_target = 100

    p = ImageProcessor(config)

    return p


@pytest.mark.parametrize(
    "positions,expected",
    [
        ([Position(5, 6, 1000), Position(5, 94, 2000)], 10),
        ([Position(0, 10, 100), Position(0, WIDTH, 110)], -math.inf),
        ([Position(10, 20, 1000), Position(98, 108, 2000)], 10),
        ([Position(100, WIDTH, 1000), Position(12, WIDTH, 2000)], 10),
        ([Position(90, WIDTH, 100), Position(0, 25, 110)], -math.inf),
        ([Position(100, 188, 1000), Position(12, 100, 2000)], 10),
    ],
)
def test_calculate_speed(empty_processor, positions, expected):
    # for width=1200px, FOV=90degrees, ft_to_target=100ft
    # 88px/1000ms should equal 10mph
    empty_processor.positions = positions
    empty_processor.calculate_speed()
    assert empty_processor.max_speed == pytest.approx(
        expected
    ), "test_calculate_speed_failed"
