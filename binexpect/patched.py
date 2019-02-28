"""This module contains patched and alternative versions of pexpect objects."""

import os
import pty
import sys

from fdpexpect import fdspawn
from pexpect import spawn

from binexpect.mixins import BinMixin, PromptMixin


# Monkey patch spawn & fdspawn to add bin support.
spawn = type("spawn", (spawn, BinMixin, PromptMixin), {})
fdspawn = type("fdspawn", (fdspawn, BinMixin, PromptMixin), {})


class ttyspawn(fdspawn):  # NOQA: N801
    """
    Like pexpect.fdspawn but provides a new tty to work with.

    This is useful for example when interacting with programs running
    under gdb --tty=X self.master and self.slave contain the file
    descriptors for the created tty.  This class has not been tested
    on anything other than Linux & BSD.
    """

    def __init__(self, verbose=False, args=[], timeout=30,
                 maxread=2000, searchwindowsize=None, logfile=None):
        """
        Initialize a tty and setup the proxied pexpect.fdspawn isntance.

        Often a new tty is created to allow for interacton by another
        program, for those cases verbose can be set to True in order
        to have the tty's name be automatically printed to stderr. The
        other agruments are identical to those of fdspawn().
        """

        self.master, self.slave = pty.openpty()
        if verbose:
            sys.stderr.write("New tty spawned at %s\r\n" % self.ttyname())
        fdspawn.__init__(self, self.master, args, timeout,
                         maxread, searchwindowsize, logfile)

    def ttyname(self):
        """Return the name of the underlying TTY."""
        return os.ttyname(self.slave)
