from setuptools import setup, find_packages

setup(
    name="llclient",
    version="1.5",
    zip_safe=False,
    packages=find_packages(),
    entry_points={"console_scripts": ["llclient = llclient.poll:main"]},
)
