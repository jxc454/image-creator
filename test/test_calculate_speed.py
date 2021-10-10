import math
import pytest
from image_creator.image_processor import ImageProcessor, Position

WIDTH = 1200


@pytest.fixture
def empty_processor():
    """Returns a Wallet instance with a zero balance"""
    p = ImageProcessor()
    p.width = WIDTH
    p.field_of_view = 90
    p.ft_to_target = 100
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
