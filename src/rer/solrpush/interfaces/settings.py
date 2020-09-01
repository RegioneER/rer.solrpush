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
        value_type=schema.Choice(vocabulary="plone.app.vocabularies.PortalTypes"),
    )

    elevate_schema = schema.SourceText(
        title=u"Elevate configuration",
        description=u"Insert a list of values for elevate. Each elevate item should"
        u' have the following structure: {"text": "some text", "ids": ["12345677"]}.',
        required=False,
        constraint=validate_cfg_json,
        default=u"[]",
    )

    index_fields = schema.SourceText(
        title=_(
            "index_fields_label",
            default=u"List of fields loaded from SOLR that we use for indexing.",
        ),
        description=_(
            u"index_fields_help",
            default=u"We store this list for performance"
            u" reasons. If the configuration changes, you need to click on"
            u" Reload button",
        ),
        required=False,
    )

    # NASCOSTO DAL PANNELLO DI CONTROLLO (vedi: browser/controlpanel.py)
    ready = schema.Bool(
        title=_(u"Ready"),
        description=_(u"SOLR push is ready to be used."),
        required=False,
        default=False,
    )


class IRerSolrpushSettings(IRerSolrpushConf):
    """
    Marker interface for settings
    """
