from setuptools import setup, find_packages


setup(
    name='dart-manager',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'click == 6.6',
        'click-log == 0.1.4',
        'PyYAML == 3.11',
        'termcolor == 1.1.0',
        'ruamel.yaml == 0.13.1'
    ],
    entry_points={
        'console_scripts': [
            'dart-manager = dart_manager:dart_manager',
        ],
    },
    package_data={
        'dart_manager': ['cli/config.yaml'],  # absent by default
    },
)