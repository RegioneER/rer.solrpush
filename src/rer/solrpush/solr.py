# -*- coding: utf-8 -*-
from plone.restapi.interfaces import ISerializeToJson
from zope.component import getMultiAdapter

import logging

logger = logging.getLogger(__name__)


def push_to_solr(item):
    """
    Perform push to solr
    """
    serializer = getMultiAdapter((item, item.REQUEST), ISerializeToJson)
    logger.info(serializer())
