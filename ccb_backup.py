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
    parser.add_argument('--post-to-s3', action='store_true', help='If specified, then the created zip file is ' +
        'posted to Amazon AWS S3 bucket (using bucket URL and password in ccb_backup.ini file)')
    parser.add_argument('--delete-zip', action='store_true', help='If specified, then the created zip file is ' +
        'deleted after posting to S3')
    parser.add_argument('--source-directory', required=False, help='If provided, then get_*.py utilities are not ' +
        'executed to create new output data, but instead files in this specified directory are used ' +
        'to zip and optionally post to AWS S3')
    parser.add_argument('--retain-temp-directory', action='store_true', help='If specified, the temp directory ' +
        'without output from get_*.py utilities is not deleted')
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

    if not g.args.post_to_s3 and g.args.delete_zip:
        message_error('Does not make sense to create zip file and delete it without posting to AWS S3. Aborting!')
        sys.exit(1)

    # If user specified a directory with set of already-created get_*.py utilities output files to use, then
    # do not run get_*.py data collection utilities, just use that
    if g.args.source_directory is not None:
        g.temp_directory = g.args.source_directory
    else:
        # Run get_XXX.py utilities into datetime_stamped CSV output files and messages_output.log output in
        # temp directory
        run_util('individuals')
        run_util('groups', ['groups', 'participants'])
        run_util('attendance', ['attendance', 'events'])
        run_util('pledges')
        run_util('contributions')

    # Create output ZIP file
    if g.args.output_filename is not None:
        output_filename = g.args.output_filename
    else:
        output_filename = './tmp/ccb_backup_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.zip'

    # zip -P "mickey" -j ./tmp/tmp.zip /var/folders/rm/y5dg__nx41l5btnph583zhvc0000gp/T/ccb_backup_KUjKbY/*
    zip_password = util.get_ini_setting('zip_file', 'password')
    exec_zip_list = ['/usr/bin/zip', '-P', zip_password, '-j', '-r', output_filename, g.temp_directory + '/']
    print exec_zip_list
    exit_status = subprocess.call(exec_zip_list)
    if exit_status == 0:
        message_info('Zipped get_*.py utilities output and messages log to ' + output_filename)
    else:
        message_warning('Error running zip. Exit status ' + str(exit_status))

    # If user specified the source directory, don't delete it!  And if user asked not to retain temp directory,
    # don't delete it!
    if g.args.source_directory is None:
        if g.args.retain_temp_directory:
            message_info('Retained temporary output directory ' + g.temp_directory)
        else:
            shutil.rmtree(g.temp_directory)
            message_info('Temporary output directory deleted')

    sys.exit(0)


def run_util(util_name, output_pair=None):
    global g

    datetime_stamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    util_py = 'get_' + util_name + '.py'
    fullpath_util_py = os.path.dirname(os.path.realpath(__file__)) + '/' + util_py
    if output_pair is not None:
        output_filename1 = g.temp_directory + '/' + output_pair[0] + '_' + datetime_stamp + '.csv'
        output_filename2 = g.temp_directory + '/' + output_pair[1] + '_' + datetime_stamp + '.csv'
        outputs_list = ['--output-' + output_pair[0] + '-filename', output_filename1,
            '--output-' + output_pair[1] + '-filename', output_filename2]
        message_info('Running ' + util_py + ' with output files ' + output_filename1 + ' and ' + \
            output_filename2)
    else:
        output_filename = g.temp_directory + '/' + util_name + '_' + datetime_stamp + '.csv'
        outputs_list = ['--output-filename', output_filename]
        message_info('Running ' + util_py + ' with output file ' + output_filename)
    exec_list = [fullpath_util_py, '--message-output-filename', g.message_output_filename] + outputs_list
    exit_status = subprocess.call(exec_list)
    if exit_status == 0:
        message_info('Successfully ran ' + util_py)
    else:
        message_warning('Error running ' + util_py + '. Exit status ' + str(exit_status))


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
