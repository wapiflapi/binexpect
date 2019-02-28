"""Monkey patches for binary transfer support in pexpect."""

from binexpect.cli import setup
from binexpect.patched import fdspawn, spawn, ttyspawn


__version__ = '0.2.0'
__author__ = 'Wannes Rombouts <wapiflapi@gmail.com>'
__all__ = [
    'spawn',
    'fdspawn',
    'ttyspawn',
    'setup',
]
