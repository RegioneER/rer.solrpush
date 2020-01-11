# -*- coding: utf-8 -*-
from rer.solrpush.interfaces.adapter import IExtractFileFromTika
from zope.interface import implementer
from rer.solrpush.solr import get_solr_connection

import json


@implementer(IExtractFileFromTika)
class FileExtractor(object):
    def __init__(self, context):
        self.context = context

    def call_solr(self, file_obj):
        solr = get_solr_connection()
        params = {
            "extractOnly": "true",
            "lowernames": "true",
            "wt": "json",
            "extractFormat": "text",
        }
        return solr._send_request(
            "post",
            "update/extract",
            body=params,
            files={"file": ('extracted', file_obj)},
        )

    def extract_from_tika(self):
        """
        """
        if not self.context.file:
            return ''
        form = self.context.REQUEST.form
        if (
            form.get('form.widgets.file', None)
            and form.get('form.widgets.file.action', '') != 'nochange'  # noqa
        ):
            # object blob hasn't already created
            file_obj = self.context.REQUEST.form['form.widgets.file']
            file_obj.seek(0)
            resp = self.call_solr(file_obj)
            file_obj.seek(0)
        else:
            file_obj = self.context.file.data
            resp = self.call_solr(file_obj)
        res = json.loads(resp)
        return res['extracted'].replace('\n', ' ').replace('\t', ' ').strip()
