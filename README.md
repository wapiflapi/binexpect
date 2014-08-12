
binexpect is a python module that monkeypatches pexpect and adds some features
that are usefull when working with binary protocols and/or exploitation.

binary sends
============

```sendbin``` and ```sendbinline``` can be used to send raw binary data.
They will escape special characters in order to avoid TTY-controling sequences.

prompt & tryexpect
==================

```prompt``` is a wrapper for ```interact``` which prints a prompt before
interacting, it also shows the escape sequence if there is one.

```tryexpect``` is a proxy for ```expect```, it prompts when an expected
pattern wasn't received before timeout. If EOF is raised by pexpect the
status of the target is checked and if it received a signal or exited it
is mentioned. If the ```exitwithprogram``` argument is not passed as False,
tryexpect will do its best to terminate itself in the same way as the target.

ttyspawn
========

This is similar to pexpect's ```fdspawn``` but will spawn a new tty to which
another program can talk. This is usefull for example when interacting with
programs running under ```gdb --tty=X```

setup
=====

```
    import binexpect

    setup = binexpect.setup("./target_program")
    target = setup.target()
```

This will give you some basic command line arguments to control what your
program is doing and to whom it is talking. You can add your own arguments to
```setup.parse```, args are available in ```setup.args``` after the target
is setup.
