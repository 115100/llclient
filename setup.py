from setuptools import setup, find_packages

setup(
    name="llclient",
    version="2.4.1",
    zip_safe=False,
    packages=find_packages(),
    entry_points={"console_scripts": ["llclient = llclient.poll:main"]},
)
