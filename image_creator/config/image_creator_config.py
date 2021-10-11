from dataclasses import dataclass


@dataclass
class ImageCreatorConfig:
    width: int
    height: int
    x_min: int
    x_max: int
    y_min: int
    y_max: int
    base_image_ttl: int
    max_time_delta: int
    min_area: int
    ft_to_target: int
    field_of_view: float
    image_buffer: int
    image_save_dir: str
    metadata_save_dir: str

    @staticmethod
    def merge(ob1, ob2):
        ob1.__dict__.update(ob2.__dict__)
        return ob1
