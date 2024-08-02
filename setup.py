from setuptools import setup, find_packages

setup(
    name='wfctl',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'wayfire',
    ],
    entry_points={
        'console_scripts': [
            'wfctl=wfctl.main:main',
        ],
    },
    author='killown',
    author_email='systemofdown@gmail.com',
    description='A command-line tool for interacting with Wayfire.',
    url='https://github.com/killown/wfctl',
)
