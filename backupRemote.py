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
import sys
import time

from pprint import pprint

from util import *

__author__  = 'Laurence Gonsalves <laurence@xenomachina.com>'

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
    parser.add_argument('-Y',
            help="""Rsync options with "formatting". This is the same as -X,
            except the "dir" currently being worked on will be inserted
            wherever %s appears.""", default=[],
            action='append')
    # TODO: make this work for non-dirs too, and fix naming?
    parser.add_argument('dirs',
            help="Directories to backup.",
            nargs='+')
    return parser

HOSTNAME_RE = re.compile(
        r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*'
        + r'([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$')

def backupRemote(runner, source, dirs, dest, unformatted_args, formatted_args):
    if not HOSTNAME_RE.match(source):
        raise UserError("%r is not a valid hostname" % source)

    for dir in dirs:
        # TODO: avoid creating double slashes (//)
        rsync_args = unformatted_args + [x % (dir,) for x in formatted_args]
        dir = re.sub(r'^/*(.*?)/*$', r'\1', dir)
        dest_dir = os.path.join(dest, dir) + '/'
        # TODO: don't use mkdir
        runner.run(['mkdir', '-p', dest_dir])
        runner.run(['rsync'] + rsync_args + ['%s:/%s/' % (source, dir)] + [dest_dir],
                # 23: Partial transfer due to error
                # 24: Partial transfer due to vanished source files
                # 25: The --max-delete limit stopped deletions
                returncode_ok={0, 23, 24, 25}.__contains__)

def main(args):
    start_time = time.time()
    runner = CommandRunner(verbose=args.verbose, dry_run=args.dry_run)
    backupRemote(runner, source=args.source, dirs=args.dirs, dest=args.dest,
            unformatted_args=args.X, dir_formatted_args=args.Y)
    print('Total running time:',
            humanReadableTimeDelta(time.time() - start_time))

if __name__ == '__main__':
    main_wrapper(create_argparser(), main)
