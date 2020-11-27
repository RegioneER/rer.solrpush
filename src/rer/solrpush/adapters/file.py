# -*- coding: utf-8 -*-
import logging
from rer.solrpush.interfaces.adapter import IExtractFileFromTika
from zope.interface import implementer

logger = logging.getLogger(__name__)


@implementer(IExtractFileFromTika)
class FileExtractor(object):
    maxfilesize = 20 * 1024 * 1024

    def __init__(self, context):
        self.context = context

    def get_file_to_index(self):
        """
        """
        if not self.context.file:
            return None
        if self.context.file.getSize() > self.maxfilesize:
            logger.warning(
                "maximun file size reached (%s > %s) for %s %s",
                self.context.file.getSize(),
                self.maxfilesize,
                self.context.absolute_url_path(),
                self.context.file.filename,
            )
            return None
        return self.context.file.data
