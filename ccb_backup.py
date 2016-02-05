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
    program_filename = None


def main(argv):
    global g

    parser = argparse.ArgumentParser()
    parser.add_argument('--output-filename', required=False,
        help='Output ZIP filename. Defaults to ./tmp/ccb_backup_[datetime_stamp].zip')
    parser.add_argument('--message-output-filename', required=False, help='Filename of message output file. If ' +
        'unspecified, then messages are written to stderr as well as into the messages_datetime_stamp].log file ' +
        'that is zipped into the resulting backup file.')
    g.args = parser.parse_args()

    g.program_filename = os.path.basename(__file__)
    if g.program_filename[-3:] == '.py':
                g.program_filename = g.program_filename[:-3]

    message_level = util.get_ini_setting('logging', 'level')

    temp_directory = tempfile.mkdtemp(prefix='ccb_backup_')

    if g.args.message_output_filename is None:
        message_output_filename = temp_directory + '/messages_' + \
            datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.log'
    else:
        message_output_filename = g.args.message_output_filename

    util.set_logger(message_level, message_output_filename, os.path.basename(__file__))

    if g.args.output_filename is not None:
        output_filename = g.args.output_filename
    else:
        output_filename = './tmp/ccb_backup_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.zip'
    
    # Gather pledges
    pledges_filename = temp_directory + '/pledges_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'
    message_info('Running get_pledges.py with output file ' + pledges_filename)
    program_filename = 'get_pledges.py'
    pledges_py = os.path.dirname(os.path.realpath(__file__)) + '/' + program_filename
    shell_result = subprocess.call([pledges_py, '--output-filename', pledges_filename, '--message-output-filename',
        message_output_filename])
    abort_if_non_zero(shell_result, program_filename, temp_directory)

    # Gather attendance and events
    attendance_filename = temp_directory + '/attendance_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'
    events_filename = temp_directory + '/events_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'
    message_info('Running get_attendance.py with output files ' + attendance_filename + ' and ' + events_filename)
    program_filename = 'get_attendance.py'
    attendance_py = os.path.dirname(os.path.realpath(__file__)) + '/' + program_filename
    shell_result = subprocess.call([attendance_py, '--output-events-filename', events_filename,
        '--output-attendance-filename', attendance_filename, '--message-output-filename', message_output_filename])
    abort_if_non_zero(shell_result, program_filename, temp_directory)

    #shutil.rmtree(temp_directory)
    sys.exit(0)


def abort_if_non_zero(shell_result, program_filename, temp_directory):
    if shell_result != 0:
        message_error(program_filename + ' failed. Aborting!')
        zip_post_and_delete(temp_directory)
        sys.exit(1)


def zip_post_and_delete(temp_directory):
    pass


def message_info(s):
    logging.info(s)
    output_message(s, 'INFO')


def message_warning(s):
    logging.warning(s)
    output_message(s, 'WARNING')


def message_error(s):
    logging.error(s)
    output_message(s, 'ERROR')


def output_message(s, level):
    global g

    if g.args.message_output_filename is None:
        datetime_stamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print >> sys.stderr, datetime_stamp + ':' + g.program_filename + ':' + level + ':' + s


if __name__ == "__main__":
    main(sys.argv[1:])
