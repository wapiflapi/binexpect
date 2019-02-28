import io
import os
import re

from setuptools import find_packages
from setuptools import setup


def read(filename):
    filename = os.path.join(os.path.dirname(__file__), filename)
    text_type = type(u"")
    with io.open(filename, mode="r", encoding='utf-8') as fd:
        return re.sub(text_type(r':[a-z]+:`~?(.*?)`'), text_type(r'``\1``'), fd.read())


setup(
    name="binexpect",
    version="0.2.0",
    url="https://github.com/wapiflapi/binexpect",
    license='MIT',

    author="Wannes Rombouts",
    author_email="wapiflapi@gmail.com",

    description="A python module that monkey patches pexpect mainly for binary transfers.",
    long_description=read("README.md"),

    packages=find_packages(exclude=('tests',)),
    package_data={'': ['LICENSE', 'README.md']},
    include_package_data=True,

    install_requires=[],

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
