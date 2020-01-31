# -*- coding: utf-8 -*-
from rer.solrpush.interfaces.adapter import IExtractFileFromTika
from zope.interface import implementer


@implementer(IExtractFileFromTika)
class FileExtractor(object):
    def __init__(self, context):
        self.context = context

    def get_file_to_index(self):
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
        else:
            file_obj = self.context.file.data
        return file_obj
