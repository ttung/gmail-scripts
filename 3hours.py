#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys

from oauth2client import client
from gmail import *

def stage():
    import time

    Service.get()

    try:
        labelid = GmailLabel.get_id("#3 hours")

        msgs = get_message_count(labelid)

        if msgs == 0:
            return

        # create a new label for the future
        now = int(time.time())
        future = now + (3 * 3600)

        staginglabelid = GmailLabel.create("postponed/UNIXTIME_" + str(future))

        def move(messages):
            relabel_messages(
                [message['id']
                 for message in messages],
                [labelid],
                [staginglabelid])

        get_messages(move, labelIds=[labelid])

    except client.AccessTokenRefreshError:
        print("The credentials have been revoked or expired, please re-run"
              "the application to re-authorize.")

def unstage():
    import time

    Service.get()

    try:
        unreadid = GmailLabel.get_id('UNREAD', system=True)
        inboxid = GmailLabel.get_id('INBOX', system=True)

        now = int(time.time())
        def matcher(name):
            splitted = name.split("postponed/UNIXTIME_")
            if len(splitted) > 1 and splitted[0] == "":
                try:
                    labeltime = int(splitted[1])
                except ValueError:
                    return False

                if labeltime < now:
                    return True
            return False

        matching_labels = GmailLabel.get_matching_ids(matcher)

        for labelid in matching_labels:
            msgs = get_message_count(labelid)

            if msgs > 0:
                def move(messages):
                    relabel_messages(
                        [message['id']
                         for message in messages],
                        [labelid],
                        [unreadid, inboxid])

                get_messages(move, labelIds=[labelid])

            GmailLabel.delete_id(labelid)

    except client.AccessTokenRefreshError:
        print("The credentials have been revoked or expired, please re-run"
              "the application to re-authorize.")

if __name__ == "__main__":
    stage()
    unstage()
