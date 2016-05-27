"""Install untz manager.

Developed on Python 3.5.1.

Usage:
    python setup.py install
"""
from setuptools import setup, find_packages

with open("requirements.txt") as fp:
    reqs = fp.read().splitlines()

setup(
    name="untz_manager",
    version="0.0.1a",
    zip_safe=False,
    packages=find_packages(),
    install_requires=reqs,
    entry_points={
        "console_scripts": [
            "untz = untz_manager.__main__:main",
        ],
    },
)
