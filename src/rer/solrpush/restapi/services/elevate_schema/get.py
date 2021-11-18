# -*- coding: utf-8 -*-
from plone.restapi.services import Service
from rer.solrpush.utils.solr_common import get_setting
from rer.solrpush.interfaces import IElevateSettings

import json


class ElevateSchemaGet(Service):
    def reply(self):
        data = get_setting(field="elevate_schema", interface=IElevateSettings)
        return json.loads(data)
