"""This module contains utility functions for dealing with terminals."""

import shlex
import subprocess


def spawn_terminal(terminal, *cmdline):
    """
    Invoke a terminal.

    There doesn't seem to be a portable way of starting a terminal.
    This works for me =)

    Args:
        terminal (str): command line to invoke a terminal.
            if this is not a command line but a command name then
            '-e' will be added before appending the cmdline.
         *cmdline: the remainder of the arguments will constitute
            the command line invoked inside the spawned terminal.

    """

    cmd = shlex.split(terminal)
    if len(cmd) == 1:
        cmd.append("-e")
    cmd.extend(cmdline)

    subprocess.Popen(cmd, stdin=None, stdout=None, stderr=None,
                     close_fds=True, shell=False)
