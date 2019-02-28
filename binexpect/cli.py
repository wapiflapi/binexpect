"""This module contains helpers used to setup argparse when using binexpect."""


import argparse
import os
import shlex

from binexpect.patched import spawn, ttyspawn
from binexpect.terminal import spawn_terminal


class Target(object):  # NOQA: N801
    """
    This uses argparse to setup a sensible CLI to configure binexpect behavior.

    Among other things it allows switching between calling a program
    directly or setting up a TTY, or to pass options to expect.

    The instantiated object has the following useful attributes:
        parser: The argparse.ArgumentParser that will be used,
            options can be added to it before calling target()
        args: After target() has been called this will contain
            the parsed arguments.

    """

    def __init__(self, command=None, args=[], timeout=30, maxread=2000,
                 searchwindowsize=None, logfile=None, cwd=None, env=None,
                 ignore_sighup=True, gdb=None, tty=None, writeback=None):
        """
        Set-up the argparse.ArgumentParser for configuring binexpect.

        Args:
            command (str): the target command to run later.
            args ([str]): Target command and arguments to be run.
            timeout (int): default timeout for reading or writing.
            maxread (int): default maximum read buffer size.
            searchwindowsize (int): how far back pexpect searches.
            logfile (file): all I/O will be logged to this file.
            cwd (str): set current working directory for target.
            env ([str]): set environ for target.
            ignore_sighup (bool): whether to ignore SIGHUP signal.
            gdb (bool): Whether to attach gdb.
            tty (bool): Whether to spawn a tty.

        """

        self.parser = argparse.ArgumentParser()

        options = self.parser.add_argument_group('binexpect options')

        options.set_defaults(command=command)  # Set default command.
        self._default_args = args  # argparse.REMAINDER doesn't have dflts.

        action = options.add_mutually_exclusive_group()
        action.add_argument(
            "-t", "--tty", action="store_true", default=tty,
            help="""
            Spawn and interact with a new TTY instead of spawning the process.
            """
        )
        action.add_argument(
            "-g", "--gdb", action="store_true", default=gdb,
            help="""
            Spawn a new new terminal running a gdb instance on the target.
            """
        )

        options.add_argument(
            "-q", "--quiet", dest="verbose", action="store_false",
            help="""
            Don't print information such as the TTY's name.
            """
        )
        options.add_argument(
            "--timeout", type=int, default=timeout,
            help="""
            If an expected message isn't received in TIMEOUT seconds
            the target program will be considered terminated.
            """
        )
        options.add_argument(
            "--nlcr", action='store_true',
            help="""
            Don't try to deactivate NLCR on the tty.
            If set, this option will cause a '\n' printed by the target
            to appear as '\r\n'.
            """
        )
        options.add_argument(
            "--delay-before-send", type=float, default=0,
            help="""
            Introduces a delay before sending something to the target,
            this is usefull to overcome bugs when for example data is send
            before the target has a chance to set echo of or stuff like that.
            """
        )
        options.add_argument(
            "--maxread", type=int, default=maxread,
            help="""
            This sets the read buffer size. This is the maximum number
            of bytes that Pexpect will try to read from a TTY at one time.
            Setting the maxread size to 1 will turn off buffering.
            """
        )
        options.add_argument(
            "--search-window-size", type=int, default=searchwindowsize,
            help="""
            This sets how far back in the incoming search buffer
            pexpect will search for pattern matches.
            """
        )
        options.add_argument(
            "--logfile", type=argparse.FileType("wb"), default=logfile,
            help="""
            Pexpect will be asked to copy all input and output
            to the given file.
            """
        )
        options.add_argument(
            "--cwd", default=cwd,
            help="""
            Sets the child process' current working directory.
            """
        )
        options.add_argument(
            "--env", default=env,
            help="""
            Sets the child process' environement.
            """
        )
        options.add_argument(
            "--ignore-sighup", action="store_true", default=ignore_sighup,
            help="""
            If set this option will cause the child process to ignore SIGHUP.
            """
        )
        options.add_argument(
            "--terminal", default=os.getenv(
                "TERMINAL", "x-terminal-emulator"),
            help="""
            specify the terminal to use, by default -e will be used
            to pass the arguments but if options are already present it
            will not be added.
            """
        )
        options.add_argument(
            "--writeback", default=writeback,
            help="""
            If a TTY is opened its name and the target's arguments will be
            written to this file. This is mainly for interfacing with debugers.
            """
        )

    def _finish_setup(self):

        # argparse.REMAINDER doesn't handle defaults, do this
        # manually with a custom action.
        default_args = self._default_args

        class AddDefaultArgs(argparse.Action):
            """Add default args if none were passed."""

            def __call__(self, parser, namespace,
                         values, option_string=None):
                if not values and default_args:
                    values = default_args[:]
                setattr(namespace, self.dest, values)

        # Those options must be added at the last moment
        # because they take the remaining arguments.
        self.parser.add_argument("command", nargs="?")
        self.parser.add_argument("args", nargs=argparse.REMAINDER,
                                 action=AddDefaultArgs)

    def target(self, args=None):
        """
        Run the target according to arguments parsed using self.parser.

        Args:
            args ([str]): args to parse. The default is taken from sys.argv.

        Returns:
            target

        """

        self._finish_setup()
        self.args = self.parser.parse_args(args)

        if self.args.tty or self.args.gdb:
            target = ttyspawn(
                verbose=self.args.verbose, args=self.args.args,
                timeout=self.args.timeout, maxread=self.args.maxread,
                searchwindowsize=self.args.search_window_size,
                logfile=self.args.logfile
            )

            command = shlex.split(self.args.command)
            binary, args = command[0], command[1:]

            if self.args.writeback is not None:
                with open(self.args.writeback, "w") as f:
                    f.write("%s\x00%s" % (target.ttyname(), "\x00".join(args)))
            if self.args.gdb:
                spawn_terminal(
                    self.args.terminal, "gdb", "-q", binary,
                    "--tty", target.ttyname()
                )
        else:
            target = spawn(
                command=self.args.command, args=self.args.args,
                timeout=self.args.timeout, maxread=self.args.maxread,
                searchwindowsize=self.args.search_window_size,
                logfile=self.args.logfile, cwd=self.args.cwd,
                env=self.args.env, ignore_sighup=self.args.ignore_sighup,
            )

        if not self.args.nlcr:
            target.setnonlcr()

        target.delaybeforesend = self.args.delay_before_send
        return target


# this lets us do `target = binexpect.cli.setup()` which makes sense.
# and this also keeps compatibility with older versions of binexpect.
setup = Target
