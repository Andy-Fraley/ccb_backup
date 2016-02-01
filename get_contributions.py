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

    contribution_detail_report_info = {
        'id':'',
        'type': 'transactions_batch_date',
        'date_range': '',
        'ignore_static_range': 'static',
        'start_date': '01/01/1990',
        'end_date': curr_date_str,
        'transactions_batch_date_number_start': '',
        'transactions_batch_date_number_end': '',
        'query_id': '',
        'transaction_type': 'all_types',
        'campus_ids': ['1'],
        'output': 'csv'
    }

    contribution_detail_request = {
        'request': json.dumps(contribution_detail_report_info),
        'output': 'export'
    }

    with requests.Session() as http_session:
        util.login(http_session, ccb_subdomain, ccb_app_username, ccb_app_password)

        # Pull back complete CSV containing detail info for every contribution in CCB database
        output_csv_header = None
        if g.args.output_filename is not None:
            output_filename = g.args.output_filename
        else:
            output_filename = './tmp/contributions_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'
        util.test_write(output_filename)
        with open(output_filename, 'wb') as csv_output_file:
            csv_writer = csv.writer(csv_output_file)
            logging.info('Note that it takes CCB a minute or two to pull retrive all contribution information')
            contribution_detail_response = http_session.post('https://' + ccb_subdomain + '.ccbchurch.com/report.php',
                data=contribution_detail_request)
            contribution_detail_succeeded = False
            if contribution_detail_response.status_code == 200 and \
                contribution_detail_response.text[:7] == 'Campus,':
                contribution_detail_succeeded = True
                csv_reader = csv.reader(StringIO.StringIO(contribution_detail_response.text.encode('ascii', 'ignore')))
                for row in csv_reader:
                    csv_writer.writerow(row)
            if not contribution_detail_succeeded:
                logging.error('Contribution Detail retrieval failed')
                sys.exit(1)
            else:
                logging.info('Contribution info successfully retrieved into file ' + output_filename)


if __name__ == "__main__":
    main(sys.argv[1:])
