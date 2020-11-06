# -*- coding: utf-8 -*-
from jsonschema import validate
from jsonschema import ValidationError
from plone.supermodel import model
from rer.solrpush import _
from zope import schema
from zope.interface import Invalid

import json

ELEVATE_SCHEMA = {
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "id": {"type": "array", "items": {"type": "string"}},
    },
}


def validate_cfg_json(value):
    """check that we have at least valid json and its a dict
    """
    try:
        jv = json.loads(value)
        if not isinstance(jv, list):
            raise Invalid(
                _(
                    "invalid_json_format",
                    "JSON is not valid. It should be a list of values.",
                )
            )
        for item in jv:
            validate(instance=item, schema=ELEVATE_SCHEMA)
    except (ValueError, ValidationError) as e:
        raise Invalid(
            _(
                "invalid_json",
                "JSON is not valid, parser complained: ${message}",
                mapping={"message": e.message},
            )
        )
    return True


class IRerSolrpushConf(model.Schema):
    """"""

    active = schema.Bool(
        title=_(u"Active"),
        description=_(u"Enable SOLR indexing on this site."),
        required=False,
        default=False,
    )

    solr_url = schema.TextLine(
        title=_(u"SOLR url"),
        description=_(u"The SOLR core to connect to."),
        required=True,
    )

    frontend_url = schema.TextLine(
        title=_(u"Frontend url"),
        description=_(u"If the website has different URL for frontend users."),
        required=False,
    )

    enabled_types = schema.List(
        title=_(u"enabled_types_label", default=u"Enabled portal types"),
        description=_(
            u"enabled_types_help",
            default=u"Select a list of portal types to index in solr. "
            u"Empty list means that all portal types will be indexed.",
        ),
        required=False,
        default=[],
        missing_value=[],
        value_type=schema.Choice(
            vocabulary="plone.app.vocabularies.PortalTypes"
        ),
    )

    elevate_schema = schema.SourceText(
        title=u"Elevate configuration",
        description=u"Insert a list of values for elevate. Each elevate item "
        u"should have the following structure: "
        u'{"text": "some text", "ids": ["12345677"]}.',
        required=False,
        constraint=validate_cfg_json,
        default=u"[]",
    )

    index_fields = schema.SourceText(
        title=_(
            "index_fields_label",
            default=u"List of fields loaded from SOLR that we use for "
            u"indexing.",
        ),
        description=_(
            u"index_fields_help",
            default=u"We store this list for performance"
            u" reasons. If the configuration changes, you need to click on"
            u" Reload button",
        ),
        required=False,
    )
    search_with_solr = schema.Bool(
        title=u"Enable search with SOLR",
        description=u"If selected, the search will be performed through SOLR "
        u"instead of Plone.",
        default=False,
        required=False,
    )
    # NASCOSTO DAL PANNELLO DI CONTROLLO (vedi: browser/controlpanel.py)
    ready = schema.Bool(
        title=_(u"Ready"),
        description=_(u"SOLR push is ready to be used."),
        required=False,
        default=False,
    )


class IRerSolrpushSearchConf(model.Schema):

    qf = schema.TextLine(
        title=_("qf_label", default=u"qf (query fields)"),
        description=_(
            "qf_help",
            default=u"Set a list of fields, each of which is assigned a boost factor "
            u"to increase or decrease that particular field’s importance in the query."
            u" For example: fieldOne^1000.0 fieldTwo fieldThree^10.0",
        ),
        required=False,
        default=u"",
    )
    bq = schema.TextLine(
        title=_("bq_label", default=u"bq (boost query)"),
        description=_(
            "bq_help",
            default=u"Set a list query clauses that will be added to the main query "
            u"to influence the score. For example if we want to boost results that"
            u' have a specific "searchwords" term: searchwords:something^1000',
        ),
        required=False,
        default=u"",
    )

    bf = schema.TextLine(
        title=_("bf_label", default=u"bf (boost functions)"),
        description=_(
            "bf_help",
            default=u"Set a list of functions (with optional boosts) that will be "
            u"used to construct FunctionQueries which will be added to the main query "
            u"as optional clauses that will influence the score. Any function "
            u"supported natively by Solr can be used, along with a boost value. "
            u"For example if we want to give less relevance to items deeper in the "
            u"tree we can set something like this: recip(path_depth,10,100,1)",
        ),
        required=False,
        default=u"",
    )


class IRerSolrpushSettings(IRerSolrpushConf, IRerSolrpushSearchConf):
    """
    Marker interface for settings
    """
