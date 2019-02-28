"""This module contains the default CLI interface for binexpect."""

import argparse

from binexpect.patched import ttyspawn


# TODO: should we use binexpect.cli.setup here ?
parser = argparse.ArgumentParser(
    description="""
    This is a python module that monkeypatches pexpect and adds support
    for raw binary comunications by escaping special characters in order
    to avoid TTY-controling sequences. This command line interfaces spawns
    a new TTY to which other programs can attach, for example gdb --tty=X.
    This is really intended to be used as a module not as CLI.""",
    epilog="""
    Written by wapiflapi@yahoo.fr, please feel free to send any comments or
    bug-reports you might have. Hosted on github.com/wapiflapi/binexpect
    """,
)

parser.add_argument(
    "--logfile", "-l", metavar="FILE",
    type=argparse.FileType("wb"), default=None,
    help="Act a bit like script - making typescript of terminal session.",
)

args = parser.parse_args()

tty = ttyspawn(verbose=True, logfile=args.logfile)

tty.prompt()
