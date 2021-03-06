import setuptools

setup = setuptools.setup

setup(
    # Application name:
    name="image-creator",
    # Version number (initial):
    version="0.1.0",
    # Application author details:
    author="jameson cotter",
    author_email="jameson.cotter@gmail.com",
    # Packages
    packages=["image_creator", "image_creator.config"],
    # Include additional files into the package
    include_package_data=True,
    # Details
    # url="http://pypi.python.org/pypi/MyApplication_v010/",
    #
    # license="LICENSE.txt",
    description="none",
    # long_description=open("README.txt").read(),
    # Dependent packages (distributions)
    install_requires=[
        "click==8.0.1; python_version >= '3.6'",
        "dacite==1.6.0",
        "importlib-resources==5.2.2",
        "numpy==1.21.2; python_version < '3.11' and python_version >= '3.7'",
        "opencv-python-headless==4.5.3.56",
        "picamera==1.13",
        "pyyaml==5.4.1",
        "typer==0.4.0",
        "zipp==3.6.0; python_version < '3.10'",
    ],
    dependency_links=[],
    entry_points={
        "console_scripts": ["image-creator=image_creator.main:image_creator"]
    },
)
