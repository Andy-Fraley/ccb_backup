#!/usr/bin/env python

import logging
import os
import ConfigParser
import string
import sys
import re
import requests
import tempfile
from xml.etree import ElementTree


def sys_exit(level=0):
    logging.shutdown()
    sys.exit(level)


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


def get_ini_setting(section, option, none_allowable=True):
    config_file_path = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + '/../ccb_backup.ini')
    if not os.path.isfile(config_file_path):
        logging.error("Required ini file '" + config_file_path + "' is missing. Clone file 'ccb_backup__sample.ini' " +
            "to create file 'ccb_backup.ini'")
        sys.exit(1)
    config_parser = ConfigParser.ConfigParser()
    config_parser.read(config_file_path)
    try:
        ret_val = config_parser.get(section, option).strip()
    except:
        ret_val = None
    if ret_val == '':
        ret_val = None
    if not none_allowable and ret_val == None:
        logging.error("Required setting in ccb_backup.ini '[" + section + ']' + option + "' cannot be missing " +
            "or blank")
        sys.exit(1)
    return ret_val


def send_email(recipient, subject, body):
    import smtplib

    gmail_user = get_ini_setting('notification_emails', 'gmail_user')
    if gmail_user is not None:
        gmail_password = get_ini_setting('notification_emails', 'gmail_password')
        if gmail_password is None:
            return

    FROM = gmail_user
    TO = recipient if type(recipient) is list else [recipient]
    SUBJECT = subject
    TEXT = body

    # Prepare actual message
    message = """\From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    server_ssl = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server_ssl.ehlo() # optional, called by login()
    server_ssl.login(gmail_user, gmail_password)
    server_ssl.sendmail(FROM, TO, message)
    server_ssl.close()


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


def ccb_rest_xml_to_temp_file(ccb_subdomain, ccb_rest_service_string, ccb_api_username, ccb_api_password):
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
        rest_api_errors = get_errors_from_rest_xml(input_filename)
        if rest_api_errors is None:
            return input_filename
        else:
            logging.error('CCB REST API call retrieval for ' + ccb_rest_service_string + ' failed with errors: '
                + rest_api_errors)
            sys.exit(1)
    else:
        logging.error('CCB REST API call retrieval for ' + ccb_rest_service_string + ' failed with HTTP status ' +
            str(response.status_code))
        sys.exit(1)


def get_errors_from_rest_xml(input_filename):
    errors_str = ''
    xml_tree = ElementTree.parse(input_filename)
    xml_root = xml_tree.getroot()
    sep = ''
    for error in xml_root.findall('./response/errors/error'):
        errors_str = errors_str + sep + error.text
        sep = '; '
    if errors_str == '':
        return None
    else:
        return errors_str


def get_elem_id_and_props(elem, list_props):
    output_list = [ elem.attrib['id'] ]
    for prop in list_props:
        sub_elem = elem.find(prop)
        if sub_elem is None or sub_elem.text is None:
            output_list.append('')
        else:
            output_list.append(sub_elem.text.encode('ascii', 'ignore'))
    return output_list
