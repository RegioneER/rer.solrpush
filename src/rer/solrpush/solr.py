# -*- coding: utf-8 -*-
from DateTime import DateTime
from lxml import etree
from plone import api
from plone.indexer.interfaces import IIndexableObject
from pysolr import SolrError
from rer.solrpush import _
from rer.solrpush.interfaces.settings import IRerSolrpushSettings
from six.moves import map
from zope.component import queryMultiAdapter
from zope.i18n import translate

import logging
import pysolr
import requests
import six
import json

logger = logging.getLogger(__name__)

ADDITIONAL_FIELDS = ['searchwords']

LUCENE_SPECIAL_CHARACTERS = '+-&|!(){}^"~?:\t\v\\/'


def fix_value(value):
    if isinstance(value, six.string_types):
        return escape_special_characters(value)
    elif isinstance(value, list):
        return list(map(escape_special_characters, value))
    logger.warning(
        '[fix_value]: unable to escape value: {}. skipping'.format(value)
    )
    return


def escape_special_characters(value):
    chars = []
    if six.PY2:
        value = value.decode('utf-8')
    for c in value:
        if c in LUCENE_SPECIAL_CHARACTERS:
            chars.append(u'\{}'.format(c))
        else:
            chars.append(c)
    new_value = u''.join(chars)
    if ' ' in new_value:
        new_value = '"{}"'.format(new_value)
    return new_value


def get_setting(field):
    return api.portal.get_registry_record(
        field, interface=IRerSolrpushSettings, default=False
    )


def set_setting(field, value):
    return api.portal.set_registry_record(
        field, interface=IRerSolrpushSettings, value=value
    )


def get_index_fields(field):
    json_str = api.portal.get_registry_record(
        field, interface=IRerSolrpushSettings, default=''
    )
    return json.loads(json_str)


def get_solr_connection():
    is_ready = get_setting(field='ready')
    solr_url = get_setting(field='solr_url')

    if not is_ready or not solr_url:
        return
    return pysolr.Solr(solr_url, always_commit=True)


def parse_date_as_datetime(value):
    """ Sistemiamo le date
    """
    if value:
        format = '%Y-%m-%dT%H:%M:%S'
        return value.utcdatetime().strftime(format) + 'Z'
    return value


def parse_date_str(value):
    return parse_date_as_datetime(DateTime(value))


def init_solr_push():
    """Inizializza la voce di registro 'index_fields'

    Lo fa leggendo il file xml di SOLR.

    :param solr_url: [required] L'url a cui richiedere il file xml
    :type solr_url: string
    :returns: Empty String if everything's good
    :rtype: String
    """
    solr_url = get_setting(field='solr_url')

    if solr_url:
        if not solr_url.endswith('/'):
            solr_url = solr_url + '/'
        try:
            respo = requests.get(solr_url + 'admin/file?file=schema.xml')
        except requests.exceptions.RequestException as err:
            ErrorMessage = 'Connection problem:\n{0}'.format(err)
            return ErrorMessage
        if respo.status_code != 200:
            ErrorMessage = 'Problems fetching schema:\n{0}\n{1}'.format(
                respo.status_code, respo.reason
            )
            return ErrorMessage

        root = etree.fromstring(respo.content)
        chosen_fields = json.dumps(
            list(map(extract_field, root.findall('.//field')))
        )
        if six.PY2:
            chosen_fields = chosen_fields.decode('utf-8')
        set_setting(field='index_fields', value=chosen_fields)
        set_setting(field='ready', value=True)
        return

    return _('No SOLR url provided')


def extract_field(node):
    field_name = node.get('name')
    field_type = node.get('type')
    if six.PY2:
        field_name = six.text_type(field_name)
        field_type = six.text_type(field_type)
    return {'id': field_name, 'type': field_type}


def is_solr_active():
    """ Just checking if solr indexing is set to active in control panel
    """
    return get_setting(field='active')


def can_index(item):
    """ Check if the item passed as argument can and has to be indexed
    """
    with api.env.adopt_roles(['Anonymous']):
        if not api.user.has_permission('View', obj=item):
            return False
    enabled_types = get_setting(field='enabled_types')
    active = get_setting(field='active')
    if not active:
        return False
    if not enabled_types:
        return True
    return item.portal_type in enabled_types


def create_index_dict(item):
    """ Restituisce un dizionario pronto per essere 'mandato' a SOLR per
    l'indicizzazione.
    """

    index_fields = get_index_fields(field='index_fields')
    frontend_url = get_setting(field='frontend_url')

    catalog = api.portal.get_tool(name='portal_catalog')
    adapter = queryMultiAdapter((item, catalog), IIndexableObject)

    index_me = {}

    for field_infos in index_fields:
        field = field_infos.get('id')
        field_type = field_infos.get('type')
        if six.PY2:
            field = field.encode('ascii')
        value = getattr(adapter, field, None)
        if not value:
            continue
        if callable(value):
            value = value()
        if isinstance(value, DateTime):
            value = parse_date_as_datetime(value)
        else:
            if field_type == 'date':
                value = parse_date_str(value)
        index_me[field] = value

    for field in ADDITIONAL_FIELDS:
        value = getattr(item, field, None)
        if value is not None:
            index_me[field] = value
    portal = api.portal.get()
    index_me['site_name'] = portal.getId()
    if frontend_url:
        index_me['url'] = item.absolute_url().replace(
            portal.portal_url(), frontend_url
        )
    return index_me


def set_sort_parameter(query):
    sort_on = query.get('sort_on')
    sort_order = query.get('sort_order', '')
    if not sort_order:
        return sort_on
    if sort_order in ['reverse']:
        return '{sort_on} desc'.format(sort_on=sort_on)
    return '{sort_on} {sort_order}'.format(
        sort_on=sort_on, sort_order=sort_order
    )


def generate_query(
    query,
    fl='',
    facets=False,
    facet_fields=['Subject', 'portal_type'],
    filtered_sites=[],
):
    """
    """
    index_fields = get_index_fields(field='index_fields')
    index_ids = [x['id'] for x in index_fields]
    solr_query = {
        'q': '',
        'fq': [],
        'facet': facets and 'true' or 'false',
        'start': query.get('b_start', 0),
        'rows': query.get('b_size', 20),
        'json.nl': 'arrmap',
    }
    for index, value in query.items():
        if index == '*':
            solr_query['q'] = '*:*'.format(value)
            continue
        if index not in index_ids:
            continue
        value = fix_value(value=value)
        if index == 'SearchableText':
            solr_query['q'] = u'SearchableText:{}'.format(value)
        else:
            solr_query['fq'].append(
                '{index}:{value}'.format(index=index, value=value)
            )
    if not solr_query['q']:
        solr_query['q'] = '*:*'
    if filtered_sites:
        solr_query['fq'].append(
            'site_name:{}'.format(' OR '.join(filtered_sites))
        )
    if 'sort_on' in query:
        solr_query['sort'] = set_sort_parameter(query)
    if facets:
        solr_query['facet.field'] = facet_fields
    if fl:
        solr_query['fl'] = fl
    return solr_query


def push_to_solr(item):
    """
    Perform push to solr
    """
    if not can_index(item):
        return
    solr = get_solr_connection()
    if not solr:
        logger.error('Unable to push to solr. Configuration is incomplete.')
        return
    index_me = create_index_dict(item)
    solr.add([index_me])


def remove_from_solr(uid):
    """
    Perform remove item from solr
    """
    solr = get_solr_connection()
    portal = api.portal.get()
    if not solr:
        logger.error('Unable to push to solr. Configuration is incomplete.')
        return
    try:
        solr.delete(q='UID:{}'.format(uid), commit=True)
    except (pysolr.SolrError, TypeError) as err:
        logger.error(err)
        message = _(
            'content_remove_error',
            default=u'There was a problem removing this content from SOLR. '
            ' Please contact site administrator.',
        )
        api.portal.show_message(
            message=message, request=portal.REQUEST, type='error'
        )


def reset_solr():
    solr = get_solr_connection()
    if not solr:
        logger.error('Unable to push to solr. Configuration is incomplete.')
        return
    solr.delete(q='*:*')


def search(**kwargs):
    solr = get_solr_connection()
    if not solr:
        msg = u'Unable to search using solr. Configuration is incomplete.'
        logger.error(msg)
        return {
            'error': True,
            'message': translate(
                _('solr_configuration_error_label', default=msg),
                context=api.portal.get().REQUEST,
            ),
        }
    solr_query = generate_query(**kwargs)
    try:
        return solr.search(**solr_query)
    except SolrError as e:
        logger.exception(e)
        return {
            'error': True,
            'message': translate(
                _(
                    'search_error_label',
                    default=u'Unable to perform a search with SOLR.'
                    u' Please contact the site administrator or wait some'
                    u' minutes.',
                ),
                context=api.portal.get().REQUEST,
            ),
        }
