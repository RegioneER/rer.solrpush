# -*- coding: utf-8 -*-
from DateTime import DateTime
from lxml import etree
from plone import api
from plone.indexer.interfaces import IIndexableObject
from rer.solrpush import _
from zope.component import queryMultiAdapter

import logging
import pysolr
import requests

logger = logging.getLogger(__name__)

DATE_FIELDS = [
    'created',
    'modified',
    'effective',
    'ModificationDate',
    'CreationDate',
]


def parse_date_as_datetime(value):
    """ Sistemiamo le date
    """
    if value:
        format = '%Y-%m-%dT%H:%M:%S'
        return value.asdatetime().strftime(format) + 'Z'
    return value


def parse_date_str(value):
    return parse_date_as_datetime(DateTime(value))


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
            ErrorMessage = "Connection problem:\n{0}".format(err)
            return ErrorMessage
        if respo.status_code != 200:
            ErrorMessage = "Problems fetching schema:\n{0}\n{1}".format(
                respo.status_code, respo.reason
            )
            return ErrorMessage

        root = etree.fromstring(respo.content)
        chosen_fields = [
            unicode(x.get("name")) for x in root.findall(".//field")
        ]

        api.portal.set_registry_record(
            'rer.solrpush.interfaces.IRerSolrpushSettings.index_fields',
            chosen_fields,
        )

        api.portal.set_registry_record(
            'rer.solrpush.interfaces.IRerSolrpushSettings.ready', True
        )

        return ""

    return _("No SOLR url provided")


def create_index_dict(item):
    """ Restituisce un dizionario pronto per essere 'mandato' a SOLR per
    l'indicizzazione.
    """

    index_fields = api.portal.get_registry_record(
        'rer.solrpush.interfaces.IRerSolrpushSettings.index_fields',
        default=False,
    )

    ascii_fields = [field.encode('ascii') for field in index_fields]

    catalog = api.portal.get_tool(name="portal_catalog")
    adapter = queryMultiAdapter((item, catalog), IIndexableObject)

    index_me = {}

    for field in ascii_fields:

        value = getattr(adapter, field, None)
        if not value:
            continue
        if callable(value):
            value = value()

        if isinstance(value, DateTime):
            value = parse_date_as_datetime(value)
        else:
            if field in DATE_FIELDS:
                value = parse_date_str(value)
        index_me[field] = value

    return index_me

# TODO: implementare delete
# TODO: è possibile con sol anche mandare un set di comandi (add+delete) in un unica volta, anzichè
#       uno alla volta, valutare le due opzioni
def push_to_solr(item):
    """
    Perform push to solr
    """

    is_ready = api.portal.get_registry_record(
        'rer.solrpush.interfaces.IRerSolrpushSettings.ready', default=False
    )

    if not is_ready:
        init_solr_push()  # TODO - no, sono dentro alla transazione

    solr_url = api.portal.get_registry_record(
        'rer.solrpush.interfaces.IRerSolrpushSettings.solr_url', default=False
    )

    index_me = create_index_dict(item)

    solr = pysolr.Solr(solr_url, always_commit=True)
    try:
        solr.add([index_me])
        message = _(
            'content_indexed_success',
            default=u'Content correctly indexed on SOLR',
        )
        api.portal.show_message(message=message, request=item.REQUEST)
    except pysolr.SolrError as err:
        logger.error(err)
        message = _(
            'content_indexed_error',
            default=u'There was a problem indexing this content. Please '
            'contact site administrator.',
        )
        # TODO: il push su solr non è necessariamente sincrono, lo statusmessage può non essere
        # la soluzione migliore per comunicare all'utente il problema di indicizzazione
        api.portal.show_message(
            message=message, request=item.REQUEST, type='error'
        )
