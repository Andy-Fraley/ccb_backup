#!/usr/bin/env python

import sys
import os
import logging
import argparse
from util import util
import boto3

# Fake class only for purpose of limiting global namespace to the 'g' object
class g:
    args = None


def main(argv):

    global g

    parser = argparse.ArgumentParser()
    parser.add_argument('--s3-filename', required=True, help='Full path (key) of file in bucket')
    parser.add_argument('--expire-time-in-secs', required=True, help='Number of seconds that accessor URL is good for')
    parser.add_argument('--message-output-filename', required=False, help='Filename of message output file. If ' +
        'unspecified, defaults to stderr')
    g.args = parser.parse_args()

    message_level = util.get_ini_setting('logging', 'level')

    util.set_logger(message_level, g.args.message_output_filename, os.path.basename(__file__))

    aws_access_key_id = util.get_ini_setting('aws', 'access_key_id', False)
    aws_secret_access_key = util.get_ini_setting('aws', 'secret_access_key', False)
    region_name = util.get_ini_setting('aws', 'region_name', False)
    bucket_name = util.get_ini_setting('aws', 's3_bucket_name', False)

    s3Client = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key,
        region_name=region_name)
    try:
        expiry_secs = int(g.args.expire_time_in_secs)
    except:
        logging.error("Invalid integer specified for --expire-time-in-secs: '" + g.args.expire_time_in_secs + "'")
        util.sys_exit(1)

    if expiry_secs <= 0:
        logging.error("Specified --expire-time-in-secs must be positive integer: '" + g.args.expire_time_in_secs + "'")
        util.sys_exit(1)

    url = s3Client.generate_presigned_url('get_object', Params = {'Bucket': bucket_name, 'Key': g.args.s3_filename},
        ExpiresIn = expiry_secs)
    print url

    util.sys_exit(0)


if __name__ == "__main__":
    main(sys.argv[1:])
