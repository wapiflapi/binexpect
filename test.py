#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tty
import sys

def clear_line(msg=""):
    sys.stdout.write("\x1b[0K%s" % msg)
    sys.stdout.flush()

def rewind_line():
    sys.stdout.write("\r")
    sys.stdout.flush()

def do_test(target, data):

    data = bytearray(data)

    if sys.version_info[0] == 2:
        data = ''.join(map(chr, data))
    else:
        rep = data = bytes(data)

    target.sendbinline(data)
    clear_line("Waiting for %r" % data[:32])
    target.expect_exact(data)
    rewind_line()

def run_tests(target):

    print("[-] Starting tests.")

    clear_line("[x] Testing simple strings.\n")

    do_test(target, b"abcd")
    do_test(target, b"abcd" * 1000)

    clear_line("[x] Testing single bytes.\n")

    for x in range(256):
        do_test(target, (x,))

    clear_line("[x] Testing single bytes in context.\n")

    for x in range(256):
        do_test(target, (61, x, 61))

    clear_line("[x] Testing multiple bytes in context.\n")

    for x in range(256):
        for y in range(256):
            do_test(target, (61, x, y, 61))

    clear_line()

if __name__ == '__main__':

    import binexpect

    setup = binexpect.setup("cat")
    target = setup.target()
    target.setecho(False)

    try:
        os.system('setterm -cursor off')
        run_tests(target)
    finally:
        os.system('setterm -cursor on')

    print("[-] Tests done.")
