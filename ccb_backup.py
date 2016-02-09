#!/usr/bin/env python

import sys
import datetime
import logging
import argparse
import os
import shutil
import tempfile
import subprocess
import ConfigParser
import re
import calendar
import boto3
from util import util
import pytz

# Fake class only for purpose of limiting global namespace to the 'g' object
class g:
    args = None
    program_filename = None
    temp_directory = None
    message_output_filename = None
    aws_access_key_id = None
    aws_secret_access_key = None
    region_name = None
    bucket_name = None


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

    # Load AWS creds which are used for checking need for backup and posting backup file
    g.aws_access_key_id = util.get_ini_setting('aws', 'access_key_id')
    g.aws_secret_access_key = util.get_ini_setting('aws', 'secret_access_key')
    g.region_name = util.get_ini_setting('aws', 'region_name')
    g.bucket_name = util.get_ini_setting('aws', 'bucket_name')

    if g.args.post_to_s3 and g.args.delete_zip:
        backups_to_do = get_backups_to_do()
        if backups_to_do is None:
            message_info('Backups in S3 are already up-to-date. Nothing to do. Exiting!')
            sys.exit(0)
        else:
            print backups_to_do

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
    zip_password = util.get_ini_setting('zip_file', 'password')
    exec_zip_list = ['/usr/bin/zip', '-P', zip_password, '-j', '-r', output_filename, g.temp_directory + '/']
    exit_status = subprocess.call(exec_zip_list)
    if exit_status == 0:
        message_info('Zipped get_*.py utilities output and messages log to ' + output_filename)
    else:
        message_warning('Error running zip. Exit status ' + str(exit_status))

    # Push ZIP file into appropriate schedule folders (daily, weekly, monthly, etc.) and then delete excess
    # backups in each folder
    if backups_to_do is not None:
        for folder_name in backups_to_do:
            if backups_to_do[folder_name]['do_backup']:
                upload_to_s3(folder_name, output_filename)
            for item_to_delete in backups_to_do[folder_name]['files_to_delete']:
                delete_from_s3(item_to_delete)

    # If user specified the source directory, don't delete it!  And if user asked not to retain temp directory,
    # don't delete it!
    if g.args.source_directory is None:
        if g.args.retain_temp_directory:
            message_info('Retained temporary output directory ' + g.temp_directory)
        else:
            shutil.rmtree(g.temp_directory)
            message_info('Temporary output directory deleted')

    sys.exit(0)


def upload_to_s3(folder_name, output_filename):
    global g

    s3_key = folder_name + '/' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.zip'
    s3 = boto3.resource('s3', aws_access_key_id=g.aws_access_key_id, aws_secret_access_key=g.aws_secret_access_key,
        region_name=g.region_name)
    data = open(output_filename, 'rb')
    bucket = s3.Bucket(g.bucket_name)
    bucket.put_object(Key=s3_key, Body=data)
    message_info('Uploaded to S3: ' + s3_key)


def delete_from_s3(item_to_delete):
    item_to_delete_key = item_to_delete.key
    item_to_delete.delete()
    print 'Deleted from S3: ' + item_to_delete_key


def get_backups_to_do():
    global g

    schedules_by_folder_name = {x['folder_name']:x for x in get_schedules_from_ini()}
    s3 = boto3.resource('s3', aws_access_key_id=g.aws_access_key_id, aws_secret_access_key=g.aws_secret_access_key,
        region_name=g.region_name)

    # In S3, folder items end with '/', whereas files do not
    file_items = [item for item in s3.Bucket(g.bucket_name).objects.all() if item.key[-1] != '/']
    files_per_folder_dict = {}
    for file_item in file_items:
        path_sects = file_item.key.split('/')
        if len(path_sects) == 2:
            if path_sects[0] in schedules_by_folder_name:
                filename = path_sects[1]
                match = re.match('([0-9]{14})\.zip', filename)
                if match is not None:
                    valid_date = True
                    try:
                        datetime.datetime.strptime(match.group(1), '%Y%m%d%H%M%S')
                    except:
                        valid_date = False
                    if valid_date:
                        if path_sects[0] not in files_per_folder_dict:
                            files_per_folder_dict[path_sects[0]] = [file_item]
                        else:
                            files_per_folder_dict[path_sects[0]].append(file_item)
                    else:
                        message_info('ZIP file with invalid datetime format...ignoring: ' + file_item.key)
                else:
                    message_info('Unrecognized file in backup folder...ignoring: ' + file_item.key)
            else:
                message_info('Unrecognized folder or file in ccb_backups S3 bucket...ignoring: ' + file_item.key)
        else:
            message_info('Unrecognized folder or file in ccb_backups S3 bucket with long path...ignoring: ' +
                file_item.key)
    backups_to_post_dict = {}
    for folder_name in schedules_by_folder_name:
        num_files_to_keep = schedules_by_folder_name[folder_name]['num_files_to_keep']
        files_to_delete = []
        do_backup = True
        if folder_name in files_per_folder_dict:
            sorted_by_last_modified_list = sorted(files_per_folder_dict[folder_name], key=lambda x: x.last_modified)
            num_files = len(sorted_by_last_modified_list)
            print "Is '" + str(sorted_by_last_modified_list[num_files - 1].last_modified) + "' greater than '" + str(schedules_by_folder_name[folder_name]['backup_after_datetime']) + "'?"
            if sorted_by_last_modified_list[num_files - 1].last_modified < schedules_by_folder_name[folder_name] \
               ['backup_after_datetime']:
                print "Nope! Setting 'do_backup' to False"
                do_backup = False
            # TODO deleted 2 out of weekly, should have deleted 3
            if num_files_to_keep > 0 and num_files >= num_files_to_keep:
                if do_backup:
                    kicker = 1
                else:
                    kicker = 0
                if num_files - num_files_to_keep + kicker > 0:
                    files_to_delete = sorted_by_last_modified_list[0:num_files - num_files_to_keep + kicker]
        print folder_name, do_backup, len(files_to_delete)
        if do_backup or len(files_to_delete) > 0:
            backups_to_post_dict[folder_name] = {'do_backup': do_backup, 'files_to_delete': files_to_delete}
    if len(backups_to_post_dict) > 0:
        return backups_to_post_dict
    else:
        return None


def get_schedules_from_ini():
    config_file_path = os.path.dirname(os.path.abspath(__file__)) + '/ccb_backup.ini'
    config_parser = ConfigParser.ConfigParser()
    config_parser.read(config_file_path)
    schedules = []
    for schedule in config_parser.items('schedules'):
        schedule_parms = schedule[1].split(',')
        if len(schedule_parms) != 3:
            message_error("ccb_backup.ini [schedules] entry '" + schedule[0] + '=' + schedule[1] + "' is invalid. " \
                "Must contain 3 comma-separated fields. Aborting!")
            sys.exit(1)
        folder_name = schedule_parms[0].strip()
        delta_time_string = schedule_parms[1].strip()
        num_files_to_keep_string = schedule_parms[2].strip()
        try:
            num_files_to_keep = int(num_files_to_keep_string)
        except:
            message_error("ccb_backup.ini [schedules] entry '" + schedule[0] + '=' + schedule[1] + "' is " \
                "invalid. '" + num_files_to_keep_string + "' must be a positive integer")
            sys.exit(1)
        if num_files_to_keep < 0:
                message_error("ccb_backup.ini [schedules] entry '" + schedule[0] + '=' + schedule[1] + "' is " \
                "invalid. Specified a negative number of files to keep")
                sys.exit(1)
        backup_after_datetime = now_minus_delta_time(delta_time_string)
        if backup_after_datetime is None:
            message_error("ccb_backup.ini [schedules] entry '" + schedule[0] + '=' + schedule[1] + "' contains " \
                "an invalid interval between backups '" + delta_time_string + "'. Aborting!")
            sys.exit(1)
        schedules.append({'folder_name': folder_name, 'backup_after_datetime': backup_after_datetime,
            'num_files_to_keep': num_files_to_keep})
    return schedules


def now_minus_delta_time(delta_time_string):
    curr_datetime = datetime.datetime.now(pytz.UTC)
    # curr_datetime = datetime.datetime(2016, 1, 7, 10, 52, 23, tzinfo=pytz.UTC)
    match = re.match('([1-9][0-9]*)([smhdwMY])', delta_time_string)
    if match is None:
        return None
    num_units = int(match.group(1))
    unit_char = match.group(2)
    seconds_per_unit = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400, 'w': 604800}
    if unit_char in seconds_per_unit:
        delta_secs = int(seconds_per_unit[unit_char]) * num_units
        return curr_datetime + datetime.timedelta(seconds=delta_secs)
    elif unit_char == 'M':
        month = curr_datetime.month - 1 + num_units
        year = int(curr_datetime.year + month / 12)
        month = month % 12 + 1
        day = min(curr_datetime.day, calendar.monthrange(year, month)[1])
        return datetime.datetime(year, month, day, curr_datetime.hour, curr_datetime.minute, curr_datetime.second,
            tzinfo=pytz.UTC)
    else: # unit_char == 'Y'
        return datetime.datetime(curr_datetime.year + num_units, curr_datetime.month, curr_datetime.day,
            curr_datetime.hour, curr_datetime.minute, curr_datetime.second, tzinfo=pytz.UTC)


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
