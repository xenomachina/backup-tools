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

from pprint import pprint

__author__  = 'Laurence Gonsalves <laurence@xenomachina.com>'

class UserError(Exception):
    def __init__(self, message):
        self.message = message

def create_argparser():
    description, epilog = __doc__.strip().split('\n', 1)
    parser = argparse.ArgumentParser(description=description, epilog=epilog,
            formatter_class=argparse.RawDescriptionHelpFormatter)
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

def main(args):
    # TODO: verify source is a hostname and ends with :
    # TODO: verify dir ends in /
    for dir in args.dirs:
        dest = os.path.join(args.dest, re.sub(r'^/*','',dir))
        pprint(['mkdir','-p',dest])
        command = ['rsync'] + args.X + [args.source + dir] + [dest]
        pprint(command)

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
