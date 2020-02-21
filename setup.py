from setuptools import setup

setup(
   name='snap-reports-backend',
   version='1.0',
   description='A simple stat backend',
   author='Martino Ferrari',
   author_email='martino.ferrari@c-s.fr',
   packages=['snap-reports-backend'],  #same as name
   install_requires=['sanic', 'numpy', 'matplotlib'], #external packages as dependencies
)