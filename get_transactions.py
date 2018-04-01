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
    util.set_logger(message_level, g.args.message_output_filename, os.path.basename(__file__))

    ccb_app_username = util.get_ini_setting('ccb', 'app_username', False)
    ccb_app_password = util.get_ini_setting('ccb', 'app_password', False)
    ccb_subdomain = util.get_ini_setting('ccb', 'subdomain', False)

    curr_date_str = datetime.datetime.now().strftime('%m/%d/%Y')

    with requests.Session() as http_session:
        util.login(http_session, ccb_subdomain, ccb_app_username, ccb_app_password)

        # Pull back complete CSV containing detail info for every transaction in CCB database
        output_csv_header = None
        if g.args.output_filename is not None:
            output_filename = g.args.output_filename
        else:
            output_filename = './tmp/transactions_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'
        util.test_write(output_filename)
        with open(output_filename, 'wb') as csv_output_file:
            csv_writer = csv.writer(csv_output_file)
            logging.info('Note that it takes CCB a minute or two to pull retrieve all transaction information')
            header_emitted = False
            # Have to only collect a year of data at a time else CCB transactions report times out.  Start with
            # year 2013 (since that's when financial data in CCB starts)
            for year in range(2013, datetime.datetime.today().year + 1):
                start_date_str = '01/01/' + str(year)
                end_date_str = '12/31/' + str(year)

                transaction_detail_report_info = {
                    "id":"",
                    "type":"transaction_detail",
                    "email_pdf":"0",
                    "is_contextual":"1",
                    "transaction_detail_type_id":"0",
                    "date_range":"",
                    "ignore_static_range":"static",
                    "start_date":start_date_str,
                    "end_date":end_date_str,
                    "campus_ids":["1"],
                    "output":"csv"
                }
                transaction_detail_request = {
                    'aj':1,
                    'ax':'run',
                    'request': json.dumps(transaction_detail_report_info)
                }

                logging.info('Retrieving info from ' + start_date_str + ' to ' + end_date_str)
                transaction_detail_response = http_session.post('https://' + ccb_subdomain + \
                    '.ccbchurch.com/report.php', data=transaction_detail_request)
                transaction_detail_succeeded = False
                if transaction_detail_response.status_code == 200:
                    if transaction_detail_response.text[:12] == 'Name,Campus,':
                        transaction_detail_succeeded = True
                        skipped_first = False
                        csv_reader = csv.reader(StringIO.StringIO(transaction_detail_response.text.encode('ascii',
                            'ignore')))
                        for row in csv_reader:
                            if not header_emitted:
                                csv_writer.writerow(row)
                                header_emitted = True
                            else:
                                if skipped_first:
                                    csv_writer.writerow(row)
                                else:
                                    skipped_first = True
                        if not transaction_detail_succeeded:
                            print transaction_detail_response
                            print transaction_detail_response.text
                            logging.error('Transaction Detail retrieval failed (will time out if too much data '
                                'retrieved)')
                            util.sys_exit(1)
                        else:
                            logging.info('Transaction info successfully retrieved into file ' + output_filename)
                    else:
                        logging.info('No CSV results returned...skipping.')

    util.sys_exit(0)


if __name__ == "__main__":
    main(sys.argv[1:])
