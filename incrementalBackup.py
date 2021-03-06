#!/usr/bin/env python
# coding=utf-8

"""
Uses backupRemote to create incremental backups.

This script is to be run on the backup server as root. When run it will create
a single, dated, backup directory. This directory will use hardlinks with the
previous backup directory.

Once the new backup has been created, older backups can also optionally be
removed. Backups have a "frequency" specified which is really just a name for a
set, though having these correspond to a backup frequency is the normal use-case.
If a maximum number for a given frequency is specified, then the older backups
for that frequency will be deleted to meet this constraint.
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
from backupRemote import backupRemote

__author__  = 'Laurence Gonsalves <laurence@xenomachina.com>'

# TODO: factor out the common stuff between this and backupRemote
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
    parser.add_argument('-T', '--timestamp',
            required=True,
            help="Time stamp for destination (YYYYMMDD-hhmmss).")
    parser.add_argument('-F', '--frequency',
            required=True,
            help="Frequency tag for backup.")
    parser.add_argument('-s', '--source',
            required=True,
            help="Source host.")
    parser.add_argument('-N', '--size-of-frequency',
            type=int,
            help='''Number of backups to keep for this frequency.  Older
            backups will be marked for deltion if this amout is exceeded.''')
    parser.add_argument('-X',
            help="Rsync options.", default=[],
            action='append')
    parser.add_argument('-Y',
            help="""Rsync options with "formatting". This is the same as -X,
            except the "dir" currently being worked on will be inserted
            wherever %s appears.""", default=[],
            action='append')
    parser.add_argument('dirs',
            help="Directories to backup.",
            nargs='+')
    return parser

TIMESTAMP_RE = (
        r'(?:19|20)\d\d'                 # year
        + r'(?:0[1-9]|1[012])'            # month
        + r'(?:0[1-9]|[12][0-9]|3[01])-'  # day
        + r'(?:[01][0-9]|2[0123])'        # hour
        + r'(?:[0-5][0-9])'               # minute
        + r'(?:[0-5][0-9])')              # second

FREQUENCY_RE = (r'[a-z0-9]+(?:-[a-z0-9]+)*')

BACKUP_RE = re.compile(
        r'^(' + TIMESTAMP_RE + r')\.(' + FREQUENCY_RE + r')$')
TIMESTAMP_RE = re.compile('^' + TIMESTAMP_RE + '$')
FREQUENCY_RE = re.compile('^' + FREQUENCY_RE + '$')

def compute_leafdir(timestamp, frequency):
    if not TIMESTAMP_RE.match(timestamp):
        raise UserError('%r is not a valid timestamp. Use YYYYMMDD-hhmmss.'
                % timestamp)
    if not FREQUENCY_RE.match(frequency):
        raise UserError('%r is not a valid frequency.' % frequency)

    return '%s.%s' % (timestamp, frequency)

IN_PROGRESS_SUFFIX = '.inprogress'
DELETING_SUFFIX = '.deleting'

def main(args):
    start_time = time.time()
    runner = CommandRunner(verbose=args.verbose, dry_run=args.dry_run)

    backup_parent = args.dest
    backup_leafdir = compute_leafdir(args.timestamp, args.frequency)
    existing = sorted([x for x in os.listdir(backup_parent)
            if BACKUP_RE.match(x) 
                and os.path.isdir(os.path.join(backup_parent, x))])
    unformatted_args = args.X
    formatted_args = args.Y
    if existing:
        if backup_leafdir <= existing[-1]:
            raise UserError('Desired name %r is less than %r'
                    % (backup_leafdir, existing[-1]))
        # TODO: turn % into %% in backup_parent and existing[-1]
        # TODO: use new-style ({}) formatting?
        formatted_args.append(
                '--link-dest=' + os.path.join(backup_parent, existing[-1], '%s'))
    rsync_dest = os.path.join(backup_parent,
            backup_leafdir + IN_PROGRESS_SUFFIX)

    backupRemote(runner, source=args.source, dirs=args.dirs, dest=rsync_dest,
            unformatted_args=unformatted_args, formatted_args=formatted_args)

    runner.mv(
            os.path.join(backup_parent, backup_leafdir + IN_PROGRESS_SUFFIX),
            os.path.join(backup_parent, backup_leafdir))

    size_of_frequency = args.size_of_frequency
    if size_of_frequency:
        in_frequency = [x for x in existing
                if BACKUP_RE.match(x).group(2) == args.frequency]
        for old_dir in in_frequency[:-args.size_of_frequency]:
            runner.mv(
                    os.path.join(backup_parent, old_dir),
                    os.path.join(backup_parent, old_dir + DELETING_SUFFIX))

    # TODO rm overflow in frequency

    print('Total running time:',
            humanReadableTimeDelta(time.time() - start_time))
    sh = CommandRunner(verbose=args.verbose, dry_run=args.dry_run)

if __name__ == '__main__':
    main_wrapper(create_argparser(), main)
