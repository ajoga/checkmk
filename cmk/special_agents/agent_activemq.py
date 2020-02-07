#!/usr/bin/env python
# -*- encoding: utf-8; py-indent-offset: 4 -*-
# +------------------------------------------------------------------+
# |             ____ _               _        __  __ _  __           |
# |            / ___| |__   ___  ___| | __   |  \/  | |/ /           |
# |           | |   | '_ \ / _ \/ __| |/ /   | |\/| | ' /            |
# |           | |___| | | |  __/ (__|   <    | |  | | . \            |
# |            \____|_| |_|\___|\___|_|\_\___|_|  |_|_|\_\           |
# |                                                                  |
# | Copyright Mathias Kettner 2014             mk@mathias-kettner.de |
# +------------------------------------------------------------------+
#
# This file is part of Check_MK.
# The official homepage is at http://mathias-kettner.de/check_mk.
#
# check_mk is free software;  you can redistribute it and/or modify it
# under the  terms of the  GNU General Public License  as published by
# the Free Software Foundation in version 2.  check_mk is  distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;  with-
# out even the implied warranty of  MERCHANTABILITY  or  FITNESS FOR A
# PARTICULAR PURPOSE. See the  GNU General Public License for more de-
# tails. You should have  received  a copy of the  GNU  General Public
# License along with GNU Make; see the file  COPYING.  If  not,  write
# to the Free Software Foundation, Inc., 51 Franklin St,  Fifth Floor,
# Boston, MA 02110-1301 USA.

from __future__ import print_function
import getopt
import sys
import xml.etree.ElementTree as ET

import requests
from requests.auth import HTTPBasicAuth


def usage():
    print("Usage:")
    print(
        "agent_activemq --servername {servername} --port {port} [--piggyback] [--username {username} --password {password}]\n"
    )


def main(sys_argv=None):
    if sys_argv is None:
        sys_argv = sys.argv[1:]

    short_options = ""
    long_options = ["piggyback", "servername=", "port=", "username=", "password="]

    try:
        opts, _args = getopt.getopt(sys_argv, short_options, long_options)
    except getopt.GetoptError as err:
        usage()
        sys.stderr.write("%s\n" % err)
        return 1

    opt_servername = None
    opt_port = None
    opt_username = None
    opt_password = None
    opt_piggyback_mode = False

    for o, a in opts:
        if o in ['--piggyback']:
            opt_piggyback_mode = True
        elif o in ['--servername']:
            opt_servername = a
        elif o in ['--port']:
            opt_port = a
        elif o in ['--username']:
            opt_username = a
        elif o in ['--password']:
            opt_password = a

    if not opt_servername or not opt_port:
        usage()
        return 1

    url = "http://%s:%s/admin/xml/queues.jsp" % (opt_servername, opt_port)

    auth = None
    if opt_username:
        auth = HTTPBasicAuth(opt_username, opt_password)

    data = []
    try:
        response = requests.get(url, auth=auth)
        if response.status_code == 401:
            raise Exception("Unauthorized")

        xml = response.text
        data = ET.fromstring(xml)
    except Exception as e:
        sys.stderr.write("Unable to connect. Credentials might be incorrect: %s\n" % e)
        return 1

    attributes = ['size', 'consumerCount', 'enqueueCount', 'dequeueCount']
    count = 0
    output_lines = []
    try:
        if not opt_piggyback_mode:
            output_lines.append("<<<mq_queues>>>")

        for line in data:
            count += 1
            if opt_piggyback_mode:
                output_lines.append("<<<<%s>>>>" % line.get('name'))
                output_lines.append("<<<mq_queues>>>")
            output_lines.append("[[%s]]" % line.get('name'))
            stats = line.findall('stats')
            values = ""
            for job in attributes:
                values += "%s " % stats[0].get(job)
            output_lines.append(values)

        if opt_piggyback_mode:
            output_lines.append("<<<<>>>>")
            output_lines.append("<<<local:sep(0)>>>")
            output_lines.append("0 Active_MQ - Found %s Queues in total" % count)
    except Exception as e:  # Probably an IndexError
        sys.stderr.write("Unable to process data. Returned data might be incorrect: %r" % e)
        return 1

    print("\n".join(output_lines))
