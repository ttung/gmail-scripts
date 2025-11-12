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
import itertools
import time

from oauth2client import client
from gmail import *


# FIXME: (ttung) get this from itertools.batched once this moves to python 3.12
def batched(iterable, n):
    # batched('ABCDEFG', 3) → ABC DEF G
    if n < 1:
        raise ValueError('n must be at least one')
    it = iter(iterable)
    while batch := tuple(itertools.islice(it, n)):
        yield batch


def main():
    Service.get()

    try:
        vault_label_id = GmailLabel.get_id('zzz')
        general_label_id = GmailLabel.get_id('zzz/general')

        def apply_vault_label(messages):
            relabel_messages(
                [message['id']
                 for message in messages],
                [],
                [vault_label_id])

        get_messages(
            apply_vault_label,
            labelIds=[],
            q='has:nouserlabels !in:inbox !in:draft !in:snoozed !label:zzz'
        )

        def apply_related_label(messages):
            service = Service.get()

            messages = {
                message['id']: {'threadId': message['threadId']}
                for message in messages
            }
            message_label_ops = []
            general_messages_ids = []

            def filter_labeled_messages_callback(message_id):
                def callback(request_id, response, exception):
                    if exception:
                        raise exception

                    for labelid in response['labelIds']:
                        # ignore the vault label
                        if labelid == vault_label_id:
                            continue
                        labelinfo = GmailLabel.get_label(labelid)
                        if labelinfo is None or labelinfo['type'] == 'user':
                            del messages[message_id]
                            break

                return callback

            # only include the messages that have other labels besides vault.
            for batch_num, batch in enumerate(
                    batched(
                        # We modify the list inside the callback, so we have to
                        # explicitly pull the message list here so we don't get
                        # the logical equivalent of a
                        # ConcurrentModificationException.
                        list(messages.keys()),
                        # We batch in groups of 10 because the gmail api quota
                        # charges "5" units for a messages.get, and there is a
                        # user quota of 250 units per second.  This ensures we
                        # stay well under the limit.
                        10,
                    )
            ):
                if batch_num != 0:
                    time.sleep(1)
                batch_req = service.new_batch_http_request()
                for message in batch:
                    request = service.users().messages().get(
                        userId='me',
                        id=message,
                        format='minimal')
                    batch_req.add(request, callback=filter_labeled_messages_callback(message))
                batch_req.execute()

            def find_thread_label(thread_id):
                def callback(request_id, response, exception):
                    if exception:
                        raise exception

                    # gather all the labels to apply to messages in this thread.
                    label_ids = set(
                        label_id
                        for message in response['messages']
                        for label_id in message['labelIds']
                    )

                    # remove non-user labels
                    label_ids.remove(vault_label_id)
                    for label_id in label_ids.copy():
                        label_info = GmailLabel.get_label(label_id)
                        if label_info is not None and label_info['type'] != 'user':
                            label_ids.remove(label_id)

                    message_ids = [
                        message_id
                        for message_id, metadata in messages.items()
                        if metadata['threadId'] == thread_id
                    ]

                    if len(label_ids) == 0:
                        general_messages_ids.extend(message_ids)
                    else:
                        message_label_ops.append((message_ids, label_ids))

                return callback

            # filter the messages that have other labels besides vault.
            batch = service.new_batch_http_request()
            for thread_id in set(metadata['threadId'] for metadata in messages.values()):
                request = service.users().threads().get(
                    userId='me',
                    id=thread_id,
                    format='minimal')
                batch.add(request, callback=find_thread_label(thread_id))
            batch.execute()

            for message_ids, label_ids in message_label_ops:
                relabel_messages(
                    message_ids,
                    [],
                    list(label_ids))
            if len(general_messages_ids) > 0:
                relabel_messages(
                    general_messages_ids,
                    [],
                    [general_label_id])

        get_messages(
            apply_related_label,
            q='label:zzz !in:inbox !in:snoozed !in:sent !label:zzz/general !label:zzz/fb')

        def clear_label(messages):
            relabel_messages(
                [message['id']
                 for message in messages],
                [vault_label_id],
                [])

        get_messages(
            clear_label,
            labelIds=[vault_label_id],
            q='older_than:60d'
        )

    except client.AccessTokenRefreshError:
        print('The credentials have been revoked or expired, please re-run'
              'the application to re-authorize.')

if __name__ == '__main__':
    main()
