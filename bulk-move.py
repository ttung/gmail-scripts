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
        #src_labelid = GmailLabel.get_id('czi-in')
        #dst_labelid = GmailLabel.get_id('vault/work/czi')
        src_labelid = GmailLabel.get_id('czi-sent')
        dst_labelid = GmailLabel.get_id('vault/work/czi/sent')

        def move(messages):
            relabel_messages(
                [message['id']
                 for message in messages],
                [src_labelid],
                [dst_labelid])

        get_messages(
            move,
            labelIds=[src_labelid],
        )

    except client.AccessTokenRefreshError:
        print('The credentials have been revoked or expired, please re-run'
              'the application to re-authorize.')

if __name__ == '__main__':
    main()
