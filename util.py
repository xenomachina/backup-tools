#!/usr/bin/env python
# coding=utf-8

"""
Utility functions/classes used for NAS backup utils.
"""

from __future__ import absolute_import, division, print_function
from future_builtins import *

import subprocess
import sys

from pprint import pprint

__author__  = 'Laurence Gonsalves <laurence@xenomachina.com>'

class UserError(Exception):
    def __init__(self, message):
        self.message = message

class CommandRunner:
    def __init__(self, verbose, dry_run):
        self.verbose = verbose
        self.dry_run = dry_run

    def v_run(self, cmd, args, returncode_ok=lambda x:x == 0):
        """
        Like run, but passes -v as first argument if verbose is true.
        """
        cmd = [cmd]
        if self.verbose:
            cmd.append('-v')
        cmd.extend(args)
        return self.run(cmd, returncode_ok)

    def run(self, args, returncode_ok=lambda x:x == 0):
        if self.verbose:
            pprint(args)
        if not self.dry_run:
            returncode = subprocess.call(args)
            if returncode_ok(returncode):
                return returncode
            else:
                raise subprocess.CalledProcessError(returncode, args)

def humanReadableTimeDelta(s, precise=False):
    t = s # units vary throughout the loop
    for factor, name in [
            (1, 'seconds'), # we start with seconds, hence 1
            (60, 'minutes'),
            (60, 'hours'),
            (24, 'days'),
            (7, 'weeks'),
            (365.25/7, 'years'),]:
        t /= factor
        if factor > 1 and t < 1: break
        result = '%g %s' % (t, name)
        if precise and t != s:
            result += ' (%g seconds)' % s
    return result

def warn(msg):
    print('WARNING: %s' % (msg,), file=sys.stderr)

def main_wrapper(argparser, main):
    error = None
    try:
        main(argparser.parse_args())
    except IOError as exc:
        if exc.errno != errno.ENOENT:
            raise
        error = '%s: %r' % (exc.strerror, exc.filename)
    except UserError as exc:
        error = exc.message

    if error is not None:
        print('%s: ERROR: %s' % (argparser.prog, error), file=sys.stderr)
        sys.exit(1)
