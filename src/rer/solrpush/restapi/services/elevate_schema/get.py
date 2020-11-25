# -*- coding: utf-8 -*-
from plone.restapi.services import Service
from rer.solrpush.utils.solr_common import get_setting
from rer.solrpush.interfaces import IElevateSettings


class ElevateSchemaGet(Service):
    def reply(self):
        return get_setting(field="elevate_schema", interface=IElevateSettings)
