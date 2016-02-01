#!/usr/bin/env python

import requests
import re
import sys
import json
import datetime
import csv
import StringIO
import logging
import argparse
import os
from util import util

# Fake class only for purpose of limiting global namespace to the 'g' object
class g:
    args = None


def main(argv):

    global g

    parser = argparse.ArgumentParser()
    parser.add_argument('--output-filename', required=False,
        help='Output CSV filename. Defaults to ./tmp/[datetime_stamp]_pledges.csv')
    parser.add_argument('--message-output-filename', required=False, help='Filename of message output file. If ' +
        'unspecified, defaults to stderr')
    g.args = parser.parse_args()

    message_level = util.get_ini_setting('logging', 'level')
    ccb_app_username = util.get_ini_setting('ccb', 'app_username')
    ccb_app_password = util.get_ini_setting('ccb', 'app_password')
    ccb_subdomain = util.get_ini_setting('ccb', 'subdomain')

    util.set_logger(message_level, g.args.message_output_filename, os.path.basename(__file__))

    curr_date_str = datetime.datetime.now().strftime('%m/%d/%Y')

    login_request = {
        'ax': 'login',
        'rurl': '/index.php',
        'form[login]': ccb_app_username,
        'form[password]': ccb_app_password
    }

    individual_detail_report_info = {
        'id':'',
        'type': 'export_individuals_change_log',
        'print_type': 'export_individuals',
        'query_id': '',
        'campus_ids': ['1']
    }

    individual_detail_request = {
        'request': json.dumps(individual_detail_report_info),
        'output': 'export'
    }

    with requests.Session() as http_session:
        util.login(http_session, ccb_subdomain, ccb_app_username, ccb_app_password)

        # Pull back complete CSV containing detail info for every individual in CCB database
        output_csv_header = None
        if g.args.output_filename is not None:
            output_filename = g.args.output_filename
        else:
            output_filename = './tmp/individuals_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'
        util.test_write(output_filename)
        with open(output_filename, 'wb') as csv_output_file:
            csv_writer = csv.writer(csv_output_file)
            logging.info('Note that it takes CCB a minute or two to pull retrive all individual information')
            individual_detail_response = http_session.post('https://' + ccb_subdomain + '.ccbchurch.com/report.php',
                data=individual_detail_request)
            individual_detail_succeeded = False
            if individual_detail_response.status_code == 200 and \
                individual_detail_response.text[:16] == '"Individual ID",':
                individual_detail_succeeded = True
                csv_reader = csv.reader(StringIO.StringIO(individual_detail_response.text.encode('ascii', 'ignore')))
                for row in csv_reader:
                    csv_writer.writerow(row)
            if not individual_detail_succeeded:
                logging.error('Individual Detail retrieval failed')
                sys.exit(1)
            else:
                logging.info('Individual info successfully retrieved into file ' + output_filename)


if __name__ == "__main__":
    main(sys.argv[1:])
