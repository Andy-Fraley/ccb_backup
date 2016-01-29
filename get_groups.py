#!/usr/bin/env python

import requests
import re
import sys
import argparse
import os
import logging
import datetime
import csv
import tempfile
from util import settings
from util import util
from xml.etree import ElementTree

# Fake class only for purpose of limiting global namespace to the 'g' object
class g:
    args = None


def main(argv):

    global g

    parser = argparse.ArgumentParser()
    parser.add_argument('--input-filename', required=False, help='Name of input XML file from previous ' +
        'group_profiles XML retrieval. If not specified, groups XML data retreived from CCB REST API.')
    parser.add_argument('--output-groups-filename', required=False, help='Name of CSV output file listing group ' +
        'information. Defaults to ./tmp/groups_[datetime_stamp].csv')
    parser.add_argument('--output-participants-filename', required=False, help='Name of CSV output file listing ' +
        'group participant information. Defaults to ./tmp/group_participants_[datetime_stamp].csv')
    parser.add_argument('--message-level', required=False, help="Either 'Info', 'Warning', or 'Error'. " +
        "Defaults to 'Warning' if unspecified. Log outputs greater or equal to specified severity are emitted " +
        "to message output.")
    parser.add_argument('--message-output-filename', required=False, help='Filename of message output file. If ' +
        'unspecified, defaults to stderr')
    parser.add_argument('--keep-temp-file', action='store_true', help='If specified, temp file created with XML ' +
        'from REST API call is not deleted')
    g.args = parser.parse_args()

    util.set_logger(g.args.message_level, g.args.message_output_filename, os.path.basename(__file__))

    # Set groups and participant filenames and test validity
    if g.args.output_groups_filename is not None:
        output_groups_filename = g.args.output_groups_filename
    else:
        output_groups_filename = './tmp/groups_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'
    util.test_write(output_groups_filename)
    if g.args.output_participants_filename is not None:
        output_participants_filename = g.args.output_participants_filename
    else:
        output_participants_filename = './tmp/group_participants_' + \
            datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'
    util.test_write(output_participants_filename)

    if g.args.input_filename is not None:
        # Pull groups XML from input file specified by user
        input_filename = g.args.input_filename
    else:
        # Pull groups XML from CCB REST API (and stash in local temp file to use as input)
        logging.info('Retrieving groups and group participants from CCB REST API. This could take minutes...')
        response = requests.get('https://ingomar.ccbchurch.com/api.php?srv=group_profiles', stream=True,
            auth=(settings.login_info.ccb_api_username, settings.login_info.ccb_api_password))
        if response.status_code == 200:
            response.raw.decode_content = True
            with tempfile.NamedTemporaryFile(delete=False) as temp:
                input_filename = temp.name
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk: # filter out keep-alive new chunks
                        temp.write(chunk)
                temp.flush()
            logging.info('Done pulling groups and group participants from CCB REST API.')
        else:
            logging.error('CCB REST API call for group_profiles failed. Aborting!')
            sys.exit(1)

    # Properties to peel off each 'group' node in XML
    list_group_props = [
        'name',
        'description',
        'campus',
        'group_type',
        'department',
        'area',
        'group_capacity',
        'meeting_day',
        'meeting_time',
        'childcare_provided',
        'interaction_type',
        'membership_type',
        'notification',
        'listed',
        'public_search_listed',
        'inactive'
    ]

    participant_nodes = [
        'ccb_api/response/groups/group/director', 'ccb_api/response/groups/group/coach',
        'ccb_api/response/groups/group/main_leader', 'ccb_api/response/groups/group/leaders/leader',
        'ccb_api/response/groups/group/participants/participant'
    ]

    path = []
    dict_path_ids = {}
    group_id = None
    logging.info('Creating groups and group participants output files.')
    with open(output_groups_filename, 'wb') as csv_output_groups_file:
        csv_writer_groups = csv.writer(csv_output_groups_file)
        csv_writer_groups.writerow(['id'] + list_group_props)
        with open(output_participants_filename, 'wb') as csv_output_participants_file:
            csv_writer_participants = csv.writer(csv_output_participants_file)
            csv_writer_participants.writerow(['group_id', 'participant_id', 'participant_type'])
            for event, elem in ElementTree.iterparse(input_filename, events=('start', 'end')):
                if event == 'start':
                    path.append(elem.tag)
                    full_path = '/'.join(path)
                    if full_path == 'ccb_api/response/groups/group':
                        current_group_id = elem.attrib['id']
                elif event == 'end':
                    if full_path == 'ccb_api/response/groups/group':
                        # Emit 'groups' row
                        props_csv = get_elem_id_and_props(elem, list_group_props)
                        csv_writer_groups.writerow(props_csv)
                        elem.clear() # Throw away 'group' node from memory when done processing it
                    elif full_path in participant_nodes:
                        # Emit 'group_participants' row
                        props_csv = [ current_group_id, elem.attrib['id'], elem.tag ]
                        csv_writer_participants.writerow(props_csv)
                    path.pop()
                    full_path = '/'.join(path)

    logging.info('Groups written to ' + output_groups_filename)
    logging.info('Group Participants written to ' + output_participants_filename)

    # If caller didn't specify input filename, then delete the temporary file we retrieved into
    if g.args.input_filename is None:
        if g.args.keep_temp_file:
            logging.info('Temporary downloaded XML retained in file: ' + input_filename)
        else:
            os.remove(input_filename)


def get_elem_id_and_props(elem, list_props):
    output_list = [ elem.attrib['id'] ]
    for prop in list_props:
        sub_elem = elem.find(prop)
        if sub_elem is None or sub_elem.text is None:
            output_list.append('')
        else:
            output_list.append(sub_elem.text.encode('ascii', 'ignore'))
    return output_list


if __name__ == "__main__":
    main(sys.argv[1:])
