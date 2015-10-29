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
    parser.add_argument('dirs',
            help="Directories to backup.",
            nargs='+')
    return parser

HOSTNAME_RE = re.compile(
        r'^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*'
        + r'([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$')

def backupRemote(runner, source, dirs, dest, rsync_args):
    if not HOSTNAME_RE.match(source):
        raise UserError("%r is not a valid hostname" % source)

    for dir in dirs:
        dir = re.sub(r'^/*(.*?)/*$', r'\1', dir)
        dest_dir = os.path.join(dest, dir) + '/'
        runner.run(['mkdir', '-p', dest_dir])
        runner.run(['rsync'] + rsync_args + ['%s:/%s/' % (source, dir)] + [dest_dir],
                # 24 means a file disappeared before we could copy it
                returncode_ok={0, 24}.__contains__)

def main(args):
    start_time = time.time()
    runner = CommandRunner(verbose=args.verbose, dry_run=args.dry_run)
    backupRemote(runner, source=args.source, dirs=args.dirs, dest=args.dest,
            rsync_args=args.X)
    print('Total running time:',
            humanReadableTimeDelta(time.time() - start_time))

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
