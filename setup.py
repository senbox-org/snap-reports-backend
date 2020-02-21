import setuptools
from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
   name='snap-reports-backend',
   version='1.0',
   description='A simple stat backend',
   long_description=long_description,
   long_description_content_type="text/markdown",
   url="https://gitlab.com/mandarancio/snap-reports-backend",
   author='Martino Ferrari',
   author_email='martino.ferrari@c-s.fr',
   packages=setuptools.find_packages(), 
   install_requires=['sanic', 'numpy', 'matplotlib'],
   scripts=[
            'scripts/updatereferences.py'
           ],
   python_requires='>=3.6'
)