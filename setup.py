"""
Alternative setup for compatibility
"""
from setuptools import setup, find_packages

setup(
    name            = 'filegen',
    version         = '0.1.4',
    packages        = find_packages(),
    python_requires = '>=3.8',
    install_requires= [
        'colorama>=0.4.4',
    ],
    entry_points={
        'console_scripts': [
            'filegen=src.cli:main',
        ],
    },
)
