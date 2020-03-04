"""Setup file for SNAP reports backend project."""
import setuptools
from setuptools import setup

with open("README.md", "r") as fh:
    DESCRIPTION = fh.read()

setup(
    name='snap_reports_backend',
    version='0.0.1',
    description='A simple stat backend',
    long_description=DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/mandarancio/snap-reports-backend",
    author='Martino Ferrari',
    author_email='martino.ferrari@c-s.fr',
    packages=setuptools.find_packages(),
    install_requires=['sanic', 'numpy', 'sanic-cors'],
    scripts=['scripts/updatereferences.py'],
    python_requires='>=3.6'
)
