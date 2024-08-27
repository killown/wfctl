from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / 'README.rst').read_text(encoding='utf-8')

setup(
    name='wfctl',
    version='0.8.4',
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
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://github.com/killown/wfctl',
)

