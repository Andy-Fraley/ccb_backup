#!/usr/bin/env python

# TODOs
#
# See big TODO at bottom of file
#
# Check this into git "backup" repository.  Make it work for CCB in general.  Release it??
#
# Add command-line args for output file
#
# Source password info outside of file (see old API utils for how to)
#
# Wrapper Python script to call get_pledges.py, get_individuals.py, etc.  Then take all results and ZIP them up
# into posted backup file into S3

import requests
import re
import sys
import json
import datetime
import csv
import StringIO
import logging
from util import settings


def main(argv):

    logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    login_request = {
        'ax': 'login',
        'rurl': '/index.php',
        'form[login]': settings.login_info.ccb_app_username,
        'form[password]': settings.login_info.ccb_app_password
    }

    curr_date_str = datetime.datetime.now().strftime('%m/%d/%Y')

    pledge_summary_report_info = {
        "id":"",
        "type":"pledge_giving_summary",
        "pledge_type":"family",
        "date_range":"",
        "ignore_static_range":"static",
        "start_date":"01/01/2000",
        "end_date":curr_date_str,
        "campus_ids":["1"],
        "output":"csv"
    }

    pledge_summary_request = {
        'request': json.dumps(pledge_summary_report_info),
        'output': 'export'
    }

    pledge_detail_report_info = {
        "type":"pledge_giving_detail",
        "id":""
    }

    pledge_detail_request = {
        'aj': 1,
        'ax': 'create_modal',
        'request': json.dumps(pledge_detail_report_info)
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
            params=pledge_detail_request)
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

        for pledge_category in list_pledge_categories:
            if pledge_category in dict_pledge_categories:
                print pledge_category, dict_pledge_categories[pledge_category]
            else:
                logging.warning('Unknown pledge category. ' + pledge_category)


if __name__ == "__main__":
    main(sys.argv[1:])
