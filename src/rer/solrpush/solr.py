# -*- coding: utf-8 -*-
from plone import api
from plone.restapi.interfaces import ISerializeToJson
from zope.component import getMultiAdapter

import logging

logger = logging.getLogger(__name__)


def push_to_solr(item):
    """
    Perform push to solr
    """

    solr_url = api.portal.get_registry_record(
        'rer.solrpush.interfaces.IRerSolrpushSettings.solr_url',
        default=False,
    )

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
