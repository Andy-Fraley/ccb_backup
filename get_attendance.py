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
from collections import defaultdict

# Fake class only for purpose of limiting global namespace to the 'g' object
class g:
    args = None


def main(argv):

    global g

    parser = argparse.ArgumentParser()
    parser.add_argument('--output-events-filename', required=False, help='Name of CSV output file listing event ' +
        'information. Defaults to ./tmp/events_[datetime_stamp].csv')
    parser.add_argument('--output-attendance-filename', required=False, help='Name of CSV output file listing ' +
        'attendance information. Defaults to ./tmp/attendance_[datetime_stamp].csv')
    parser.add_argument('--message-level', required=False, help="Either 'Info', 'Warning', or 'Error'. " +
        "Defaults to 'Warning' if unspecified. Log outputs greater or equal to specified severity are emitted " +
        "to message output.")
    parser.add_argument('--message-output-filename', required=False, help='Filename of message output file. If ' +
        'unspecified, defaults to stderr')
    g.args = parser.parse_args()

    util.set_logger(g.args.message_level, g.args.message_output_filename, os.path.basename(__file__))

    # Set events and attendance filenames and test validity
    if g.args.output_events_filename is not None:
        output_events_filename = g.args.output_events_filename
    else:
        output_events_filename = './tmp/events_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'
    util.test_write(output_events_filename)
    if g.args.output_attendance_filename is not None:
        output_attendance_filename = g.args.output_attendance_filename
    else:
        output_attendance_filename = './tmp/attendance_' + \
            datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.csv'
    util.test_write(output_attendance_filename)

    # Pull event profiles XML from CCB REST API (and stash in local temp file to use as input)
    logging.info('Retrieving event profiles from CCB REST API')
    response = requests.get('https://ingomar.ccbchurch.com/api.php?srv=event_profiles', stream=True,
        auth=(settings.login_info.ccb_api_username, settings.login_info.ccb_api_password))
    if response.status_code == 200:
        response.raw.decode_content = True
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            input_filename = temp.name
            for chunk in response.iter_content(chunk_size=1024):
                if chunk: # filter out keep-alive new chunks
                    temp.write(chunk)
            temp.flush()
        logging.info('Done pulling event profiles from CCB REST API.')
    else:
        logging.error('CCB REST API call for event_profiles failed. Aborting!')
        sys.exit(1)

    # Properties to peel off each 'event' node in XML
    list_event_props = [
        'name',
        'description',
        'leader_notes',
        'start_datetime',
        'end_datetime',
        'timezone',
        'recurrence_description',
        'approval_status',
        'listed',
        'public_calendar_listed'
    ] # Also collect event_id, group_id, organizer_id

    path = []
    dict_list_event_names = defaultdict(list)
    logging.info('Creating events output file')
    with open(output_events_filename, 'wb') as csv_output_events_file:
        csv_writer_events = csv.writer(csv_output_events_file)
        csv_writer_events.writerow(['event_id'] + list_event_props + ['group_id', 'organizer_id']) # Write header row
        for event, elem in ElementTree.iterparse(input_filename, events=('start', 'end')):
            if event == 'start':
                path.append(elem.tag)
                full_path = '/'.join(path)
                if full_path == 'ccb_api/response/events/event':
                    current_event_id = elem.attrib['id']
            elif event == 'end':
                if full_path == 'ccb_api/response/events/event':
                    # Emit 'events' row
                    props_csv = get_elem_id_and_props(elem, list_event_props)
                    event_id = props_csv[0] # get_elem_id_and_props() puts 'id' prop at index 0
                    name = props_csv[1] # Cheating here...we know 'name' prop is index 1
                    dict_list_event_names[name].append(event_id)
                    props_csv.append(current_group_id)
                    props_csv.append(current_organizer_id)
                    csv_writer_events.writerow(props_csv)
                    elem.clear() # Throw away 'event' node from memory when done processing it
                elif full_path == 'ccb_api/response/events/event/group':
                    current_group_id = elem.attrib['id']
                elif full_path == 'ccb_api/response/events/event/organizer':
                    current_organizer_id = elem.attrib['id']
                path.pop()
                full_path = '/'.join(path)

    logging.info('Events written to ' + output_events_filename)
    print dict_list_event_names.items()
    # logging.info('Group Participants written to ' + output_attendance_filename)

    # Remove temp file holding retrieved event_profiles XML
    # os.remove(input_filename)
    logging.info('Left event_profiles XML temp file in place. ' + input_filename)


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
