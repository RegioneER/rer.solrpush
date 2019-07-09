# -*- coding: utf-8 -*-
from lxml import etree
from plone import api
from plone.restapi.interfaces import ISerializeToJson
from rer.solrpush import _
from zope.component import getMultiAdapter

import logging
import requests


logger = logging.getLogger(__name__)


def init_solr_push(solr_url):
    """Inizializza la voce di registro 'index_fields'

    Lo fa leggendo il file xml di SOLR.

    :param solr_url: [required] L'url a cui richiedere il file xml
    :type solr_url: string
    :returns: Empty String if everything's good
    :rtype: String
    """

    print solr_url

    if solr_url:
        if not solr_url.endswith("/"):
            solr_url = solr_url + "/"
        respo = requests.get(solr_url + 'admin/file?file=schema.xml')
        if respo.status_code != 200:
            ErrorMessage = "Problems fetching schema:\n{0}\n{1}".format(
                respo.status_code,
                respo.reason,
            )
            return ErrorMessage

        root = etree.fromstring(respo.content)
        chosen_fields = [
            unicode(x.get("name"))
            for x in root.findall(".//field")
        ]

        api.portal.set_registry_record(
            'rer.solrpush.interfaces.IRerSolrpushSettings.index_fields',
            chosen_fields,
        )

        api.portal.set_registry_record(
            'rer.solrpush.interfaces.IRerSolrpushSettings.ready',
            True,
        )

        return ""

    return _("No SOLR url provided")


def push_to_solr(item):
    """
    Perform push to solr
    """

    is_ready = api.portal.get_registry_record(
        'rer.solrpush.interfaces.IRerSolrpushSettings.ready',
        default=False,
    )

    if not is_ready:
        init_solr_push()

    # CHECK: Se il site_id resta obbligatorio nella configurazione del prodotto
    # allora non c'è bisogno di fare questo 'or'
    site_id = api.portal.get_registry_record(
        'rer.solrpush.interfaces.IRerSolrpushSettings.site_id'
    ) or api.portal.get().id

    serializer = getMultiAdapter((item, item.REQUEST), ISerializeToJson)

    # TODO - push dei dati su SOLR (POST)
    import pdb; pdb.set_trace()
    logger.info("***ESEGUITO IL PUSH!***")  # TODO rimuovere riga
    logger.info(serializer())
