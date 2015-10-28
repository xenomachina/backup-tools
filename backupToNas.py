#!/usr/bin/env python
# coding=utf-8

"""
Backs up files to NAS.

This script is to be run on the NAS as root.
"""

from __future__ import absolute_import, division, print_function
from future_builtins import *

import argparse
import os
import re
import subprocess
import sys
import time

from pprint import pprint

__author__  = 'Laurence Gonsalves <laurence@xenomachina.com>'

class UserError(Exception):
    def __init__(self, message):
        self.message = message

def create_argparser():
    description, epilog = __doc__.strip().split('\n', 1)
    parser = argparse.ArgumentParser(description=description, epilog=epilog,
            formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-n', '--dry-run',
            action='store_true',
            help="Perform dry-run.")
    parser.add_argument('-v', '--verbose',
            action='store_true',
            help="Increase verbosity.")
    parser.add_argument('-d', '--dest',
            required=True,
            help="Destination directory.")
    parser.add_argument('-s', '--source',
            required=True,
            help="Source host.")
    parser.add_argument('-X',
            help="Rsync options.", default=[],
            action='append')
    parser.add_argument('dirs',
            help="Directories to backup.",
            nargs='+')
    return parser

HOSTNAME_RE = re.compile(
        r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*'
        + r'([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$')

class CommandRunner:
    def __init__(self, verbose, dry_run):
        self.verbose = verbose
        self.dry_run = dry_run

    def run(self, args):
        if self.verbose:
            pprint(args)
        if not self.dry_run:
            subprocess.check_call(args)

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

def main(args):
    start_time = time.time()
    if not HOSTNAME_RE.match(args.source):
        raise UserError("%r is not a valid hostname" % args.source)

    sh = CommandRunner(verbose=args.verbose, dry_run=args.dry_run)

    for dir in args.dirs:
        dir = re.sub(r'^/*(.*?)/*$', r'\1', dir)
        dest = os.path.join(args.dest, dir) + '/'
        sh.run(['mkdir', '-p', dest])
        sh.run(['rsync'] + args.X + ['%s:/%s/' % (args.source, dir)] + [dest])
    print('Total running time:',
            humanReadableTimeDelta(time.time() - start_time))

def warn(msg):
    print('WARNING: %s' % (msg,), file=sys.stderr)

if __name__ == '__main__':
    error = None
    argparser = create_argparser()
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
