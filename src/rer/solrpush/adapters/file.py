# -*- coding: utf-8 -*-
from plone import api
from rer.solrpush.interfaces.adapter import IExtractFileFromTika
from zope.interface import implementer


try:
    from collective.limitfilesizepanel.interfaces import ILimitFileSizePanel

    HAS_LFSP = True
except ImportError:
    HAS_LFSP = False

import logging


logger = logging.getLogger(__name__)


@implementer(IExtractFileFromTika)
class FileExtractor(object):
    def __init__(self, context):
        self.context = context

    def maxfilesize(self):
        max_size = 30
        if HAS_LFSP:
            try:
                file_size = api.portal.get_registry_record(
                    "file_size", interface=ILimitFileSizePanel
                )
                if file_size:
                    max_size = file_size
            except Exception:
                pass  # we use our default
        return max_size * 1024 * 1024

    def get_file_to_index(self):
        """ """
        file_obj = getattr(self.context, "file", None)
        if not file_obj:
            return None
        max_size = self.maxfilesize()
        if file_obj.getSize() > max_size:
            logger.warning(
                "Maximun file size reached (%s > %s) for %s %s",
                file_obj.getSize(),
                max_size,
                self.context.absolute_url_path(),
                file_obj.filename,
            )
            return None
        try:
            return file_obj.data
        except Exception as e:
            # generic because can be a PoskeyError raised also by RelStorage and we could not have it here.
            # this is raised if we are creating a new object, because there isn't the blob yet.
            # this is not a problem, because the file is in dictionary
            logger.debug(e)
            return None
