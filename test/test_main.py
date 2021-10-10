import yaml
from image_creator import main


def test_main():
    with open("config/production.yaml", "r") as stream:
        config = yaml.safe_load(stream)
        print(config.get("camera"))

        main.hello("x")
