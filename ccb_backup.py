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
    temp_directory = None
    message_output_filename = None


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

    g.temp_directory = tempfile.mkdtemp(prefix='ccb_backup_')

    if g.args.message_output_filename is None:
        g.message_output_filename = g.temp_directory + '/messages_' + \
            datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.log'
    else:
        g.message_output_filename = g.args.message_output_filename

    util.set_logger(message_level, g.message_output_filename, os.path.basename(__file__))

    if g.args.output_filename is not None:
        output_filename = g.args.output_filename
    else:
        output_filename = './tmp/ccb_backup_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.zip'
    
    # Run get_XXX.py utilities into datetime_stamped CSV output files and messages_output.log output in temp directory
    run_util('individuals')
    run_util('groups', ['groups', 'participants'])
    run_util('attendance', ['attendance', 'events'])
    run_util('pledges')
    run_util('contributions')

    #shutil.rmtree(temp_directory)
    sys.exit(0)


def run_util(util_name, output_pair=None):
    global g

    datetime_stamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    if output_pair is not None:
        output_filename1 = g.temp_directory + '/' + output_pair[0] + '_' + datetime_stamp + '.csv'
        output_filename2 = g.temp_directory + '/' + output_pair[1] + '_' + datetime_stamp + '.csv'
        outputs_list = ['--output-' + output_pair[0] + '-filename', output_filename1,
            '--output-' + output_pair[1] + '-filename', output_filename2]
        message_info('Running get_' + util_name + '.py with output files ' + output_filename1 + ' and ' + \
            output_filename2)
    else:
        output_filename = g.temp_directory + '/' + util_name + '_' + datetime_stamp + '.csv'
        outputs_list = ['--output-filename', output_filename]
        message_info('Running get_' + util_name + '.py with output file ' + output_filename)
    util_py = 'get_' + util_name + '.py'
    fullpath_util_py = os.path.dirname(os.path.realpath(__file__)) + '/' + util_py
    exec_list = [fullpath_util_py, '--message-output-filename', g.message_output_filename] + outputs_list
    print exec_list
    shell_result = subprocess.call(exec_list)
    abort_if_non_zero(shell_result, util_py, g.temp_directory)


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
