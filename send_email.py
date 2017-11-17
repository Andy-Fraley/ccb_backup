#!/usr/bin/env python

import sys
import argparse
from util import util


def main(argv):
    global g

    parser = argparse.ArgumentParser()
    parser.add_argument('--email-address', required=True, nargs='*', help='List of one or more email addresses ' \
        'to send to')
    parser.add_argument('--subject', required=False, help='Email subject')
    parser.add_argument('--body', required=False, help='Email body')
    parser.add_argument('--include-ip', action='store_true', help='If specified, then local IP address is appended ' \
        'to the outgoing email')

    args = parser.parse_args()

    if args.body is not None:
        body = args.body
    else:
        body = ''

    if args.subject is not None:
        subject = args.subject
    else:
        subject = ''

    if args.include_ip:
        body += '\r\n\r\nSent from local IP address ' + util.get_ip_address()

    util.send_email(args.email_address, subject, body)

    util.sys_exit(0)


if __name__ == "__main__":
    main(sys.argv[1:])
