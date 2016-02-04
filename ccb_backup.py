#!/usr/bin/env python

import sys
import datetime
import logging
import argparse
import os
import shutil
import tempfile
import subprocess
from util import util

# Fake class only for purpose of limiting global namespace to the 'g' object
class g:
    args = None


def main(argv):

    global g

    parser = argparse.ArgumentParser()
    parser.add_argument('--output-filename', required=False,
        help='Output ZIP filename. Defaults to ./tmp/ccb_backup_[datetime_stamp].zip')
    parser.add_argument('--message-output-filename', required=False, help='Filename of message output file. If ' +
        'unspecified, defaults to stderr')
    g.args = parser.parse_args()

    message_level = util.get_ini_setting('logging', 'level')

    util.set_logger(message_level, g.args.message_output_filename, os.path.basename(__file__))

    if g.args.output_filename is not None:
        output_filename = g.args.output_filename
    else:
        output_filename = './tmp/ccb_backup_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.zip'
    temp_directory = tempfile.mkdtemp(prefix='ccb_backup_')
    
    message_output_filename = temp_directory + '/messages_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.log'
    print message_output_filename
    pledges_filename = temp_directory + '/pledges_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'
    print pledges_filename
    logging.info('Running get_pledges.py with output file ' + pledges_filename)
    print os.path.basename(__file__) + '/get_pledges.py'
    pledges_py = os.path.dirname(os.path.realpath(__file__)) + '/get_pledges.py'
    subprocess.call([pledges_py, '--output-filename', pledges_filename, '--message-output-filename',
        message_output_filename])
    #shutil.rmtree(temp_directory)
    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv[1:])
