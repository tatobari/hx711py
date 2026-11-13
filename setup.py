from setuptools import setup, find_packages

setup(
    name='hx711',
    version='0.6.0',
    description='HX711 Python Library for Raspberry Pi',
    packages=find_packages(include=['hx711', 'hx711.*']),
    install_requires=['RPi.GPIO'],
    python_requires='>=3',
)
