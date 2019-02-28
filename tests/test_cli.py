"""This module has tests for binexpect.cli.setup."""

import sys

import pytest

import binexpect


@pytest.mark.parametrize("cmd, sysargs, newargs, expected", [
    (None, [], None, None),
    ("cat", [], None, "cat"),
    (None, ["foo"], None, "foo"),
    ("cat", ["foo"], None, "foo"),
    (None, [], ["bar"], "bar"),
    ("cat", [], ["bar"], "bar"),
    (None, ["foo"], ["bar"], "bar"),
    ("cat", ["foo"], ["bar"], "bar"),
])
def test_setup_cmd(cmd, sysargs, newargs, expected):
    """Test basic setup command."""

    oldargs = sys.argv

    # Add the "program name" to argv.
    sysargs.insert(0, "test")
    sys.argv = sysargs

    setup = binexpect.cli.setup(cmd)
    setup._finish_setup()

    parsedargs = setup.parser.parse_args(newargs)
    assert parsedargs.command == expected
    sys.argv = oldargs


@pytest.mark.parametrize("tgargs, sysargs, newargs, expected", [
    (None, [], None, []),
    (["a", "b"], [], None, ["a", "b"]),
    (None, ["cmd"], None, []),
    (None, ["cmd", "c", "d"], None, ["c", "d"]),
    (None, [], ["cmd"], []),
    (None, [], ["cmd", "c", "d"], ["c", "d"]),

    # default args overwritten by sysargs.
    (["a", "b"], ["cmd"], None, ["a", "b"]),
    (["a", "b"], ["cmd", "c", "d"], None, ["c", "d"]),

    # default args overwritten by parsed args..
    (["a", "b"], [], ["cmd"], ["a", "b"]),
    (["a", "b"], [], ["cmd", "c", "d"], ["c", "d"]),

    # sys args overwritten by parsed args.
    (None, ["cmd", "a", "b"], ["cmd", "c", "d"], ["c", "d"]),

    # default and sys args overwritten by parsed args.
    (["x", "y"], ["cmd", "a", "b"], ["cmd", "c", "d"], ["c", "d"]),
])
def test_setup_args(tgargs, sysargs, newargs, expected):
    """Test basic setup arguments."""

    oldargs = sys.argv

    # Add the "program name" to argv.
    sysargs.insert(0, "test")
    sys.argv = sysargs

    setup = binexpect.cli.setup("cat", args=tgargs)
    setup._finish_setup()

    print(setup.parser.get_default("args"))
    parsedargs = setup.parser.parse_args(newargs)
    assert parsedargs.args == expected
    sys.argv = oldargs


@pytest.mark.parametrize("tty", [None, True, False])
@pytest.mark.parametrize("writeback", [True, False])
def test_target_defaults_args(tty, writeback, tmp_path):
    """Test target instantiating."""

    if writeback:
        writeback = tmp_path / "writeback"
    else:
        writeback = None

    setup = binexpect.cli.setup("cat")

    args = []
    if tty:
        args.append("--tty")
    if writeback:
        args.append("--writeback=%s" % (tmp_path / "writeback"))

    target = setup.target(args)

    if tty:
        assert isinstance(target, binexpect.patched.ttyspawn)
        if writeback is not None:
            pid = writeback.open("r").read()
            assert pid == target.ttyname() + "\x00"
    else:
        assert isinstance(target, binexpect.patched.spawn)


@pytest.mark.parametrize("tty", [True, False])
def test_target_basic_functionality(tty):
    """Test very basic functionality."""

    setup = binexpect.cli.setup("cat")
    target = setup.target([] if not tty else ["--tty"])
    target.setecho(False)

    target.sendline(b"simple test")
    target.tryexpect(b"simple (.*)\n")
    assert target.match.group(1) == b"test"
