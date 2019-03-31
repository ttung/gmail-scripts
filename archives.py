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
        personal_mail_labelid = GmailLabel.get_id('vault/personal-mail')

        def apply_personal_mail_label(messages):
            service = Service.get()
            batch = service.new_batch_http_request()

            apply_queue = []
            def make_callback(message_id):
                def callback(request_id, response, exception):
                    if exception:
                        raise exception

                    for labelid in response['labelIds']:
                        # ignore the vault label
                        if labelid == vault_labelid:
                            continue
                        labelinfo = GmailLabel.get_label(labelid)
                        if labelinfo is None or labelinfo['type'] == 'user':
                            break
                    else:
                        # include this in the apply queue.
                        apply_queue.append((message_id, response))

                return callback

            for message in messages:
                request = service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='minimal')
                batch.add(request, callback=make_callback(message['id']))

            batch.execute()

            if len(apply_queue) > 0:
                relabel_messages(
                    [messageid
                     for messageid, _ in apply_queue],
                    [],
                    [personal_mail_labelid])

        get_messages(
            apply_personal_mail_label,
            q='label:vault !in:inbox !in:snoozed !label:vault/personal-mail !label:vault/fb')

        def apply_both_labels(messages):
            relabel_messages(
                [message['id']
                 for message in messages],
                [],
                [vault_labelid])

        get_messages(
            apply_both_labels,
            labelIds=[],
            q='(has:nouserlabels OR label:vault/fb) !in:inbox !in:draft !in:snoozed !label:vault newer_than:14d'
        )

        def clear_label(messages):
            relabel_messages(
                [message['id']
                 for message in messages],
                [vault_labelid],
                [])

        get_messages(
            clear_label,
            labelIds=[vault_labelid],
            q='older_than:14d'
        )

    except client.AccessTokenRefreshError:
        print('The credentials have been revoked or expired, please re-run'
              'the application to re-authorize.')

if __name__ == '__main__':
    main()
