from setuptools import setup, find_packages  # type: ignore

setup(
    name="llclient",
    version="2.3.0",
    zip_safe=False,
    packages=find_packages(),
    entry_points={"console_scripts": ["llclient = llclient.poll:main"]},
)
