# coding: utf-8

"""This module provides mixins monkeypatching pexpect for binary features."""

import contextlib
import copy
import os
import signal
import sys
import termios

import pexpect


splash = '''
      ▄▄▄·▄▄▌ ▐ ▄▌ ▐ ▄ ▄▄▄ .·▄▄▄▄      ▄• ▄▌.▄▄ · ▪   ▐ ▄  ▄▄ •
     ▐█ ▄███· █▌▐█•█▌▐█▀▄.▀·██▪ ██     █▪██▌▐█ ▀. ██ •█▌▐█▐█ ▀ ▪
      ██▀·██▪▐█▐▐▌▐█▐▐▌▐▀▀▪▄▐█· ▐█▌    █▌▐█▌▄▀▀▀█▄▐█·▐█▐▐▌▄█ ▀█▄
     ▐█▪·•▐█▌██▐█▌██▐█▌▐█▄▄▌██. ██     ▐█▄█▌▐█▄▪▐█▐█▌██▐█▌▐█▄▪▐█
     .▀    ▀▀▀▀ ▀▪▀▀ █▪ ▀▀▀ ▀▀▀▀▀•      ▀▀▀  ▀▀▀▀ ▀▀▀▀▀ █▪·▀▀▀▀
 ▄▄▄▄    ██▓ ███▄    █ ▓█████ ▒██   ██▒ ██▓███  ▓█████  ▄████▄  ▄▄▄█████▓
▓█████▄ ▓██▒ ██ ▀█   █ ▓█   ▀ ▒▒ █ █ ▒░▓██░  ██▒▓█   ▀ ▒██▀ ▀█  ▓  ██▒ ▓▒
▒██▒ ▄██▒██▒▓██  ▀█ ██▒▒███   ░░  █   ░▓██░ ██▓▒▒███   ▒▓█    ▄ ▒ ▓██░ ▒░
▒██░█▀  ░██░▓██▒  ▐▌██▒▒▓█  ▄  ░ █ █ ▒ ▒██▄█▓▒ ▒▒▓█  ▄ ▒▓▓▄ ▄██▒░ ▓██▓ ░
░▓█  ▀█▓░██░▒██░   ▓██░░▒████▒▒██▒ ▒██▒▒██▒ ░  ░░▒████▒▒ ▓███▀ ░  ▒██▒ ░
░▒▓███▀▒░▓  ░ ▒░   ▒ ▒ ░░ ▒░ ░▒▒ ░ ░▓ ░▒▓▒░ ░  ░░░ ▒░ ░░ ░▒ ▒  ░  ▒ ░░
▒░▒   ░  ▒ ░░ ░░   ░ ▒░ ░ ░  ░░░   ░▒ ░░▒ ░      ░ ░  ░  ░  ▒       ░
 ░    ░  ▒ ░   ░   ░ ░    ░    ░    ░  ░░          ░   ░          ░
 ░       ░           ░    ░  ░ ░    ░              ░  ░░ ░ @wapiflapi
------░------------------------------------------------░-----------------
- Powered by pexpect, works best with linux and gxf -
-------------------------------------------------------------------------
'''


class TLIST(object):
    """Indexes for termios list."""

    IFLAG, OFLAG, CFLAG, LFLAG, ISPEED, OSPEED, CC = range(7)


# Why the fuck is this not already available in signal?
SIGNALS = dict((getattr(signal, n), n)
               for n in dir(signal) if n.startswith('SIG') and '_' not in n)


class BinMixin(object):
    """
    This mixin adds support for raw binary communications.

    This is done by escaping special characters in order to avoid
    TTY-controling sequences. This use the .send() and .sendline()
    methods of the base class.
    """

    def setmode(self, fd, when, mode):
        """
        Call tcsetattr on the specified fd.

        This also monkeypatches pexpect's internal attributes
        according to the changes when it's needed.
        """

        # TODO: Check if this code is still needed/relevant.
        if mode[TLIST.OFLAG] & termios.ONLCR:
            self.crlf = pexpect.spawn.crlf
        else:
            self.crlf = pexpect.spawn.crlf[-1]

            termios.tcsetattr(fd, when, mode)

    @contextlib.contextmanager
    def changemode(self, when=termios.TCSADRAIN):
        """
        Context manager for easy modification of TTY attributes.

        A stack of previous modes is maintained.

        Args:
            when: forwarded to termios.tcsetattr

        Returns:
            dict: mode that can be modified and will be set.

        """

        if not hasattr(self, "oldmodes"):
            self.oldmodes = []

        fd = self.fileno()
        mode = termios.tcgetattr(fd)
        self.oldmodes.append(copy.deepcopy(mode))

        yield mode  # this list will be modified by user.

        if mode == self.oldmodes[-1]:
            self.oldmodes[-1] = None
        else:
            self.setmode(fd, when, mode)

    def restoremode(self, when=termios.TCSADRAIN):
        """
        Restore the previous mode from the stack maintained by changemode.
        """

        fd = self.fileno()
        mode = self.oldmodes.pop()
        if mode is not None:
            self.setmode(fd, when, mode)

    def setnlcr(self):
        """
        Set NLCR in the underlying TTY's output flags.
        """

        with self.changemode() as mode:
            mode[TLIST.OFLAG] = mode[TLIST.OFLAG] | termios.ONLCR

    def setnonlcr(self):
        """
        Clear NLCR in the underlying TTY's output flags.
        """

        with self.changemode() as mode:
            mode[TLIST.OFLAG] = mode[TLIST.OFLAG] & ~termios.ONLCR

    def escape(self, s):
        """
        Add escape sequences to s so it can be transmitted 'as is'.

        This is used to avoid a string triggering terminal control
        sequences without the need to activate raw mode.
        """

        escaped = bytearray(len(s) * 2)

        for i, c in enumerate(s):
            # Some background:
            # According to ASCCI 16 is DLE (data link escape) which would
            # make sense. Except the thing is I mistyped it as 0x16 one
            # day and things sudently started to work. So, please don't
            # touch this unless you know what you are doing more than me.
            #
            # For the reccord 0x16 is Synchronous Idle (SYN) which should
            # have nothing to do with escaping stuff. In caret notation
            # 0x16 is ^v and that is used to type strange characters in a
            # shell so I guess it *kinda* makes sense but I have no idea why.
            escaped[i * 2] = 0x16
            escaped[i * 2 + 1] = c if isinstance(c, int) else ord(c)

        return bytes(escaped)

    def sendbin(self, s):
        """
        Escape the string then send it.
        """
        return self.send(self.escape(s))

    def sendbinline(self, s=''):
        """
        Escape the string then send it as a line.
        """
        return self.sendline(self.escape(s))


class PromptMixin(object):
    """This MixIn allows to print a prompt when interacting with a target."""

    def _check_target(self, exitwithprogram):
        """Check if target is alive, maybe stop in the same way."""

        # Careful now, self might not have signal/exit status.
        if getattr(self, "signalstatus") is not None:
            sys.stdout.write(
                "Program received signal %d. (%s)\r\n" % (
                    self.signalstatus,
                    SIGNALS.get(self.signalstatus, "Unknown"))
            )
            if exitwithprogram:
                sys.stdout.write("Killing ourself with same signal.\r\n")
                os.kill(os.getpid(), self.signalstatus)

            return False  # target is dead.

        if getattr(self, "exitstatus") is not None:
            sys.stdout.write(
                "Program exited with status %d.\r\n" % (
                    self.exitstatus)
            )
            if exitwithprogram:
                sys.stdout.write("Exiting with same status.\r\n")
                exit(self.exitstatus)

            return False  # target is dead.

        return True

    def prompt(self, prompt=None, escape_character=chr(29),
               input_filter=None, output_filter=None,
               echo=True,
               print_escape_character=True,
               exitwithprogram=True):
        """
        Call self.interact() after printing a prompt.
        """

        oldecho = self.getecho()
        if echo is not None:
            self.setecho(echo)

        # If this is binMixin we are nice.
        # We temporarily activate nlcr on behalf of the user.
        binmixin = isinstance(self, BinMixin)
        if binmixin:
            self.setnlcr()

        if sys.stdout.isatty():
            if print_escape_character:
                sys.stdout.write("Escape character is '^%c'\r\n" % (
                    ord(escape_character) + 64))
            if prompt is not None:
                sys.stdout.write(prompt)

        self.interact(
            escape_character=escape_character,
            input_filter=input_filter,
            output_filter=output_filter,
        )

        if self.isalive():
            # Our job is done, cleanup and getout.
            if binmixin:
                self.restoremode()
            if echo is not None and echo != oldecho:
                self.setecho(oldecho)
            return

        self._check_target(exitwithprogram)

    def pwned(self, *args, **kwargs):
        """
        Call self.interact() after printing a bad-ass prompt.
        """

        if sys.stdout.isatty():
            sys.stdout.write(splash)
        # We just pwned the thing. Don't let it kill us.
        self.prompt(*args, exitwithprogram=False, **kwargs)

    def tryexpect(self, pattern, timeout=None, searchwindowsize=None,
                  exitwithprogram=True):
        """Proxy expect with basic error handling.

        Prompts when an expected pattern wasn't received before timeout.

        If EOF is raised by pexpect the status of the target is
        checked and if it received a signal or exited then that fact
        is mentioned.

        If the exitwithprogram argument is not set to False, tryexpect
        will do its best to terminate itself in the same way as the
        target.

        """

        try:
            return self.expect(pattern, timeout, searchwindowsize)
        except pexpect.TIMEOUT:
            self.prompt("Didn't receive expected %r.\r\n" % pattern)
            sys.stdout.write("Continuing script.\r\n")
        except pexpect.EOF:
            if self.isalive():
                raise
            if self._check_target(exitwithprogram):
                raise
