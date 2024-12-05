# -*- coding: utf-8 -*-
from plone.app.vocabularies.catalog import CatalogSource as CatalogSourceBase
from plone.supermodel import model
from rer.solrpush import _
from zExceptions import BadRequest
from zope import schema
from zope.globalrequest import getRequest
from zope.i18n import translate
from zope.interface import Invalid
from zope.interface import invariant

import json


class CatalogSource(CatalogSourceBase):
    """
    Without this hack, validation doesn't pass
    """

    def __contains__(self, value):
        return True  # Always contains to allow lazy handling of removed objs


class IElevateSettings(model.Schema):
    """ """

    elevate_schema = schema.SourceText(
        title=_("elevate_schema_label", default="Elevate configuration"),
        description=_(
            "elevate_schema_help",
            default="Insert a list of values for elevate.",
        ),
        required=False,
    )

    @invariant
    def elevate_invariant(data):
        elevate_schema = json.loads(data.elevate_schema)
        request = getRequest()
        words_mapping = [x["keywords"] for x in elevate_schema]
        for i, schema_item in enumerate(elevate_schema):
            keywords = schema_item.get("keywords", [])
            if not keywords:
                raise Invalid(
                    translate(
                        _(
                            "text_required_label",
                            default="Text field must be filled for Group ${id}.",
                            mapping=dict(id=i + 1),
                        ),
                        context=request,
                    )
                )
            for text in keywords:
                for words_i, words in enumerate(words_mapping):
                    if i == words_i:
                        # it's the current config
                        continue
                    if text in words:
                        raise BadRequest(
                            translate(
                                _(
                                    "text_duplicated_label",
                                    default='"${text}" is used in several groups.',
                                    mapping=dict(id=i, text=text),
                                ),
                                context=request,
                            )
                        )
