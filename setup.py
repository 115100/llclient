"""Install untz manager.

Developed on Python 3.5.1.

Usage:
    python setup.py install
"""
from setuptools import setup, find_packages

from untz_manager import __version__

with open("requirements.txt") as fp:
    REQS = fp.read().splitlines()

setup(
    name="untz_manager",
    version=__version__,
    zip_safe=False,
    packages=find_packages(),
    install_requires=REQS,
    entry_points={
        "console_scripts": [
            "untz = untz_manager.__main__:main",
        ],
    },
)
