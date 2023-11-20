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

def main():
    Service.get()

    try:
        labelid = GmailLabel.get_id('meta/bounced-from-trash')
        inbox_labelid = GmailLabel.get_id('INBOX', system=True)
        trash_labelid = GmailLabel.get_id('TRASH', system=True)

        get_messages(
            lambda messages: relabel_messages(
                [message['id']
                 for message in messages],
                [trash_labelid],
                [inbox_labelid, labelid]),
            q='in:trash from:tonytung !to:plans@tripit.com !label:meta/bounced-from-trash')

        get_messages(
            lambda messages: relabel_messages(
                [message['id']
                 for message in messages],
                [trash_labelid],
                [inbox_labelid, labelid]),
            q='in:trash !from:tonytung@merly.org has:userlabels !label:meta/read-once !label:meta/bounced-from-trash !label:meta/likely-spam')

    except client.AccessTokenRefreshError:
        print('The credentials have been revoked or expired, please re-run'
              'the application to re-authorize.')

if __name__ == '__main__':
    main()
