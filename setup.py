from setuptools import setup, find_packages

setup(
    name='hx711',
    version='0.6.0',
    description='HX711 Python Library for Raspberry Pi',
    packages=find_packages(include=['hx711', 'hx711.*']),
    extras_require={
        'rpi': ['RPi.GPIO'],
        'dev': ['pytest'],
    },
    python_requires='>=3',
)
