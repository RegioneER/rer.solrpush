# -*- coding: utf-8 -*-
"""Init and utils."""
from plone import api
from zope.i18nmessageid import MessageFactory

import lxml
import requests


_ = MessageFactory('rer.solrpush')


class RerSolrpushSchemaConf(object):
    """
    fields: la lista di tutti gli indici specificati su solr
    solr_url: l'url di accesso al server di solr

    is_ready(): per sapere se l'istanza è usabile
    """

    def init(self):
        self.solr_url = api.portal.get_registry_record(
            'rer.solrpush.interfaces.IRerSolrpushSettings.solr_url',
            default=False,
        )
        self.fields = None

    def is_ready(self):
        if self.solr_url and self.fields:
            return True
        return False

    def load_schema_file(self):
        if self.is_ready():
            file_url = self.solr_url + "admin/file?file=schema.xml"
            response = requests.get(file_url)
            doc = lxml.html.fromstring(response.content)
            # TODO - leggere tutti i field da indicizzare dall'xml
        else:
            return False
