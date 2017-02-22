#!/usr/bin/env python

import sys

from googleapiclient import sample_tools

class Service(object):
    service = None

    @classmethod
    def get(cls):
        if cls.service is None:
            cls.service, _ = sample_tools.init(
                sys.argv, 'gmail', 'v1', __doc__, __file__,
                scope='https://www.googleapis.com/auth/gmail.modify')

        return cls.service

class GmailLabel(object):
    cache = None
    revcache = None
    systemcache = None
    systemrevcache = None

    @classmethod
    def _populate_cache(cls):
        result = Service.get().users().labels().list(userId='me').execute()

        cls.cache = {labelentry['name'] : labelentry['id']
                     for labelentry in result['labels']
                     if labelentry['type'] == 'user'}
        cls.revcache = {labelentry['id'] : labelentry['name']
                        for labelentry in result['labels']
                        if labelentry['type'] == 'user'}
        cls.systemcache = {labelentry['name'] : labelentry['id']
                           for labelentry in result['labels']
                           if labelentry['type'] == 'system'}
        cls.systemrevcache = {labelentry['id'] : labelentry['name']
                              for labelentry in result['labels']
                              if labelentry['type'] == 'system'}

    @classmethod
    def _ensure_cache(cls, invalidate=False):
        if cls.cache is None or invalidate:
            cls._populate_cache()

    @classmethod
    def get_id(cls, name, system=False, invalidate=False):
        cls._ensure_cache(invalidate=invalidate)

        if system:
            return cls.systemcache[name]
        else:
            return cls.cache[name]

    @classmethod
    def get_label(cls, labelid, invalidate=False):
        cls._ensure_cache(invalidate=invalidate)

        if labelid in cls.revcache:
            return {
                'name': cls.revcache[labelid],
                'type': 'user',
            }
        elif labelid in cls.systemrevcache:
            return {
                'name': cls.systemrevcache[labelid],
                'type': 'system',
            }

    @classmethod
    def get_matching_ids(cls, predicate, system=False, invalidate=False):
        cls._ensure_cache(invalidate=invalidate)

        if system:
            src = cls.systemcache
        else:
            src = cls.cache

        return [labelid
                for name, labelid in src.items()
                if predicate(name)]

    @classmethod
    def create(cls, name):
        if cls.cache is not None and name in cls.cache:
            return cls.cache[name]

        result = Service.get().users().labels().create(
            userId='me',
            body={
                'name': name,
            },
        ).execute()

        cls.cache[name] = result['id']
        cls.revcache[result['id']] = name

        return result['id']

    @classmethod
    def delete_id(cls, labelid):
        result = Service.get().users().labels().delete(
            userId='me', id=labelid).execute()

        labelname = cls.revcache.get(labelid)
        if labelname:
            del cls.cache[labelname]
            del cls.revcache[labelid]

def get_message_count(labelid):
    result = Service.get().users().messages().list(
        userId='me',
        labelIds=[labelid]).execute()

    return result['resultSizeEstimate']

def get_messages(callback, **search_params):
    page_token = None
    while True:
        result = Service.get().users().messages().list(
            userId='me',
            pageToken=page_token,
            **search_params).execute()

        if result.get('messages'):
            callback(result['messages'])

        if result.get('nextPageToken'):
            page_token = result['nextPageToken']
        else:
            break

def relabel_messages(message_ids, remove_labels, add_labels):
    result = Service.get().users().messages().batchModify(
        userId='me',
        body={
            'removeLabelIds': remove_labels,
            'ids': message_ids,
            'addLabelIds': add_labels,
        }).execute()
