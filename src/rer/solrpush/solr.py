# -*- coding: utf-8 -*-
# from DateTime import DateTime
from datetime import datetime
from lxml import etree
from plone import api
from plone.restapi.interfaces import ISerializeToJson
from rer.solrpush import _
from zope.component import getMultiAdapter

import logging
import pysolr
import requests

logger = logging.getLogger(__name__)


# def parseDate(value):
#     """ Presa da collective.solr :)
#
#     Use `DateTime` to parse a date, but take care of solr 1.4
#         stripping away leading zeros for the year representation
#     """
#     if value.find('-') < 4:
#         year, rest = value.split('-', 1)
#         value = '%04d-%s' % (int(year), rest)
#     return DateTime(value)


def parse_date_as_datetime(value):
    """ Sistemiamo le date
    """
    if value:
        if value.find('-') < 4:
            year, rest = value.split('-', 1)
            value = '%04d-%s' % (int(year), rest)
        if value.endswith('00:00'):
            value = value[:-6]
            value += "Z"
        format = '%Y-%m-%dT%H:%M:%S'
        if '.' in value:
            format += '.%fZ'
        else:
            format += 'Z'

        return datetime.strptime(value, format)
    return value


def init_solr_push(solr_url):
    """Inizializza la voce di registro 'index_fields'

    Lo fa leggendo il file xml di SOLR.

    :param solr_url: [required] L'url a cui richiedere il file xml
    :type solr_url: string
    :returns: Empty String if everything's good
    :rtype: String
    """

    if solr_url:
        if not solr_url.endswith("/"):
            solr_url = solr_url + "/"
        try:
            respo = requests.get(solr_url + 'admin/file?file=schema.xml')
        except requests.exceptions.RequestException as err:
            ErrorMessage = "Connection problem:\n{0}".format(
                err,
            )
            return ErrorMessage
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


def create_index_dict(serialized, index_fields):
    """ Restituisce un dizionario pronto per essere 'mandato' a SOLR per
    l'indicizzazione.
    """

    ascii_fields = [field.encode('ascii') for field in index_fields]
    date_fields = ['created', 'modified', 'effective']

    index_me = {}

    for field in ascii_fields:
        if field in date_fields:
            index_me[field] = parse_date_as_datetime(serialized.get(field))
            print("\n\n{}\n\n".format(parse_date_as_datetime(serialized.get(field))))  # noqa TODO togliere
        else:
            index_me[field] = serialized.get(field) or serialized.get(field.lower())  # noqa

    return index_me


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

    solr_url = api.portal.get_registry_record(
        'rer.solrpush.interfaces.IRerSolrpushSettings.solr_url',
        default=False,
    )

    index_fields = api.portal.get_registry_record(
        'rer.solrpush.interfaces.IRerSolrpushSettings.index_fields',
        default=False,
    )

    # TODO - push dei dati su SOLR (POST)
    index_me = create_index_dict(serializer(), index_fields)

    solr = pysolr.Solr(solr_url, always_commit=True)
    try:
        solr.add([index_me])
        logger.info("***ESEGUITO IL PUSH!***")  # TODO rimuovere riga
    except pysolr.SolrError as err:
        logger.error(err)

    logger.info(serializer())  # TODO rimuovere riga
