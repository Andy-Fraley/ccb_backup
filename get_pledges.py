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
from util import settings
from util import util

# Fake class only for purpose of limiting global namespace to the 'g' object
class g:
    args = None


def main(argv):

    global g

    parser = argparse.ArgumentParser()
    parser.add_argument('--output-filename', required=False,
        help='Output CSV filename. Defaults to ./tmp/[datetime_stamp]_pledges.csv')
    parser.add_argument('--message-level', required=False, help="Either 'Info', 'Warning', or 'Error'. " +
        "Defaults to 'Warning' if unspecified. Log outputs greater or equal to specified severity are emitted " +
        "to message output.")
    parser.add_argument('--message-output-filename', required=False, help='Filename of message output file. If ' +
        'unspecified, defaults to stderr')
    g.args = parser.parse_args()

    util.set_logger(g.args.message_level, g.args.message_output_filename, os.path.basename(__file__))

    curr_date_str = datetime.datetime.now().strftime('%m/%d/%Y')

    login_request = {
        'ax': 'login',
        'rurl': '/index.php',
        'form[login]': settings.login_info.ccb_app_username,
        'form[password]': settings.login_info.ccb_app_password
    }

    pledge_summary_report_info = {
        "id":"",
        "type":"pledge_giving_summary",
        "pledge_type":"family",
        "date_range":"",
        "ignore_static_range":"static",
        "start_date":"01/01/1990",
        "end_date":curr_date_str,
        "campus_ids":["1"],
        "output":"csv"
    }

    pledge_summary_request = {
        'request': json.dumps(pledge_summary_report_info),
        'output': 'export'
    }

    pledge_detail_dialog_report_info = {
        "type":"pledge_giving_detail",
        "id":""
    }

    pledge_detail_dialog_request = {
        'aj': 1,
        'ax': 'create_modal',
        'request': json.dumps(pledge_detail_dialog_report_info),
    }

    pledge_detail_report_info = {
        'id':'',
        'type': 'pledge_giving_detail',
        'transaction_detail_type_id': '{coa_id}', # {coa_id} is substituted at run-time
        'print_type': 'family',
        'split_child_records': '1',
        'show': 'all',
        'date_range': '',
        'ignore_static_range': 'static',
        'start_date': '01/01/1990',
        'end_date': curr_date_str,
        'campus_ids': ['1'],
        'output': 'csv'
    }

    pledge_detail_request = {
        'request': json.dumps(pledge_detail_report_info), # This is also replaced at run-time
        'output': 'export'
    }

    with requests.Session() as http_session:
        # Login
        login_response = http_session.post('https://ingomar.ccbchurch.com/login.php', data=login_request)
        login_succeeded = False
        if login_response.status_code == 200:
            match_login_info = re.search('individual: {\s+id: 5,\s+name: "' + settings.login_info.ccb_app_login_name +
                '"', login_response.text)
            if match_login_info != None:
                login_succeeded = True
        if not login_succeeded:
            logging.error('Login to CCB app using username ' + settings.login_info.ccb_app_username +
                ' failed. Aborting!')
            sys.exit(1)

        # Get list of pledged categories
        pledge_summary_response = http_session.post('https://ingomar.ccbchurch.com/report.php',
            data=pledge_summary_request)
        pledge_summary_succeeded = False
        if pledge_summary_response.status_code == 200:
            match_pledge_summary_info = re.search('COA Category', pledge_summary_response.text)
            if match_pledge_summary_info != None:
                pledge_summary_succeeded = True
        if not pledge_summary_succeeded:
            logging.error('Pledge Summary retrieval failure. Aborting!')
            sys.exit(1)
        csv_reader = csv.reader(StringIO.StringIO(pledge_summary_response.text.encode('ascii', 'ignore')))
        header_row = True
        list_pledge_categories = []
        for row in csv_reader:
            if header_row:
                assert row[0] == 'COA Category'
                header_row = False
            else:
                list_pledge_categories.append(unicode(row[0]))

        # Get dictionary of category option IDs
        report_page = http_session.get('https://ingomar.ccbchurch.com/service/report_settings.php',
            params=pledge_detail_dialog_request)
        if report_page.status_code == 200:
            match_report_options = re.search(
                '<select\s+name=\\\\"transaction_detail_type_id\\\\"\s+id=\\\\"\\\\"\s*>(.*?)<\\\/select>',
                report_page.text)
            pledge_categories_str = match_report_options.group(1)
        else:
            logging.error('Error retrieving report settings page. Aborting!')
            sys.exit(1)
        dict_pledge_categories = {}
        root_str = ''
        for option_match in re.finditer(r'<option\s+value=\\"([0-9]+)\\"\s*>([^<]*)<\\/option>',
            pledge_categories_str):
            if re.match(r'&emsp;', option_match.group(2)):
                dict_pledge_categories[root_str + ' : ' + option_match.group(2)[6:]] = int(option_match.group(1))
            else:
                root_str = option_match.group(2)
                dict_pledge_categories[root_str] = int(option_match.group(1))

        # Loop over each category with pledges and pull back CSV list of pledges for that category
        output_csv_header = None
        if g.args.output_filename is not None:
            output_filename = g.args.output_filename
        else:
            output_filename = './tmp/pledges_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'
        util.test_write(output_filename)
        with open(output_filename, 'wb') as csv_output_file:
            csv_writer = csv.writer(csv_output_file)
            for pledge_category in list_pledge_categories:
                logging.info('Retrieving pledges for ' + pledge_category)
                if pledge_category in dict_pledge_categories:
                    pledge_detail_report_info['transaction_detail_type_id'] = \
                        str(dict_pledge_categories[pledge_category])
                    pledge_detail_request['request'] = json.dumps(pledge_detail_report_info)
                    pledge_detail_response = http_session.post('https://ingomar.ccbchurch.com/report.php',
                        data=pledge_detail_request)
                    pledge_detail_succeeded = False
                    if pledge_detail_response.status_code == 200 and pledge_detail_response.text[:8] == 'Name(s),':
                        pledge_detail_succeeded = True
                        csv_reader = csv.reader(StringIO.StringIO(pledge_detail_response.text.encode('ascii',
                            'ignore')))
                        header_row = True
                        for row in csv_reader:
                            if header_row:
                                header_row = False
                                if output_csv_header is None:
                                    output_csv_header = ['COA ID', 'COA Category'] + row
                                    amount_column_index = output_csv_header.index('Total Pledged')
                                    csv_writer.writerow(output_csv_header)
                            else:
                                row = [dict_pledge_categories[pledge_category], pledge_category] + row
                                if row[amount_column_index] != '0': # Ignore non-pledge (contrib-only) rows
                                    csv_writer.writerow(row)
                    if not pledge_detail_succeeded:
                        logging.warning('Pledge Detail retrieval failure for category ' + pledge_category)
                else:
                    logging.warning('Unknown pledge category. ' + pledge_category)

    logging.info('Retrieval of pledge detail completed successfully')


if __name__ == "__main__":
    main(sys.argv[1:])
