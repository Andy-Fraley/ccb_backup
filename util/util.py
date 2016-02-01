#!/usr/bin/env python

import logging
import os
import ConfigParser
import string
import sys
import re


def set_logger(message_level='Warning', message_output_filename=None, program_filename=None):
    # Set logging level
    if message_level is not None:
        if message_level not in ['Info', 'Warning', 'Error']:
            logging.error("Specified message level '" + str(message_level) +
                "' must be 'Info', 'Warning', or 'Error'")
            sys.exit(1)
    else:
        message_level = 'Warning'
    logging_map = {
        'Info': logging.INFO,
        'Warning': logging.WARNING,
        'Error': logging.ERROR
    }
    logging.getLogger().setLevel(logging_map[message_level])

    # Set output filename (or leave as stderr) and format
    if message_output_filename is not None:
        if program_filename is not None:
            if program_filename[-3:] == '.py':
                program_filename = program_filename[:-3]
            logging.basicConfig(filename=message_output_filename, format='%(asctime)s:%(levelname)s:' +
                program_filename + ':%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        else:
            logging.basicConfig(filename=message_output_filename, format='%(asctime)s:%(levelname)s:%(message)s',
                datefmt='%Y-%m-%d %H:%M:%S')
    else:
        logging.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S')


def test_write(filename):
    try:
        test_file_write = open(filename, 'wb')
    except:
        logging.error("Cannot write to file '" + filename + "'")
        sys.exit(1)
    else:
        test_file_write.close()
        os.remove(filename)



def get_ini_setting(section, option):
    config_file_path = os.path.dirname(os.path.abspath(__file__)) + '/../ccb_backup.ini'
    config_parser = ConfigParser.ConfigParser()
    config_parser.read(config_file_path)
    ret_val = config_parser.get(section, option).strip()
    if ret_val == '':
        ret_val = None
    return ret_val


def login(http_session, ccb_subdomain, ccb_app_username, ccb_app_password):

    login_request = {
        'ax': 'login',
        'rurl': '/index.php',
        'form[login]': ccb_app_username,
        'form[password]': ccb_app_password
    }

    login_response = http_session.post('https://' + ccb_subdomain + '.ccbchurch.com/login.php', data=login_request)
    login_succeeded = False
    if login_response.status_code == 200:
        match_login_info = re.search('<a href="/logout.php">Logout</a>', login_response.text)
        if match_login_info != None: # If we find logout anchor link in response, then we know login was successful
            login_succeeded = True
    if not login_succeeded:
        logging.error('Login to CCB app using username ' + ccb_app_username + ' failed. Aborting!')
        sys.exit(1)


def ccb_rest_xml_to_temp_file(ccb_subdomain, ccb_rest_service_string, ccb_api_username, ccb_api_password,
    check_string=None):

    logging.info('Retrieving ' + ccb_rest_service_string + ' from CCB REST API')
    response = requests.get('https://' + ccb_subdomain + '.ccbchurch.com/api.php?srv=' + ccb_rest_service_string,
        stream=True, auth=(ccb_api_username, ccb_api_password))
    if response.status_code == 200:
        response.raw.decode_content = True
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            input_filename = temp.name
            for chunk in response.iter_content(chunk_size=1024):
                if chunk: # filter out keep-alive new chunks
                    temp.write(chunk)
            temp.flush()
        return input_filename
    else:
        logging.warning('CCB REST API call retrieval for ' + ccb_rest_service_string + ' failed')
        return None
