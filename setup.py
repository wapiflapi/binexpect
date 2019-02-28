"""This module contains the setuptools setup for installation."""


from setuptools import find_packages
from setuptools import setup


setup(
    name="binexpect",
    version="0.2.0",
    url="https://github.com/wapiflapi/binexpect",
    license='MIT',

    author="Wannes Rombouts",
    author_email="wapiflapi@gmail.com",

    description="Monkey patches for binary transfer support in pexpect.",
    long_description=open("README.md").read(),

    packages=find_packages(exclude=('tests',)),
    package_data={'': ['LICENSE', 'README.md']},
    include_package_data=True,

    install_requires=[
        'pexpect==4.6.0',
    ],

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
