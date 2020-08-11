"""
Setup.py file.
Install once-off with:  "pip install ."
For development:        "pip install -e .[dev]"
"""

import setuptools

# with open("requirements.txt") as f:
#     install_requires = f.read().splitlines()

setuptools.setup(
    name="ada_tools",
    version="0.1",
    description="Satelite image preprocessing utilities",
    packages=setuptools.find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        'tqdm',
        'click',
        'bs4',
        'fiona',
        'rasterio',
        'shapely',
        'geopandas',
        'shutil',
        'neat-EO'
    ],
    extras_require={
        'dev': [  # Place NON-production dependencies in this list - so for DEVELOPMENT ONLY!
            "jupyterlab",
            "black",
            "flake8",
        ],
    },
)
