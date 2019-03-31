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
        vault_labelid = GmailLabel.get_id('vault')
        inbox_labelid = GmailLabel.get_id('INBOX', system=True)
        sent_inboxed_labelid = GmailLabel.get_id('meta/sent-inboxed')

        def apply_labels(messages):
            """
            Apply the INBOX and meta/sent-inboxed labels to the messages.
            """
            relabel_messages(
                [message['id'] for message in messages],
                [],
                [inbox_labelid, sent_inboxed_labelid, vault_labelid])

        get_messages(
            apply_labels,
            q='in:Sent !label:meta/sent-inboxed newer_than:1d')

        def clear_label(messages):
            """
            Remove meta/sent-inboxed from messages.
            """
            relabel_messages(
                [message['id'] for message in messages],
                [sent_inboxed_labelid],
                [])

        get_messages(
            clear_label,
            q='label:meta/sent-inboxed older_than:2d'
        )

    except client.AccessTokenRefreshError:
        print('The credentials have been revoked or expired, please re-run'
              'the application to re-authorize.')

if __name__ == '__main__':
    main()
