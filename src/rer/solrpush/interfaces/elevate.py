# -*- coding: utf-8 -*-
from plone.app.vocabularies.catalog import CatalogSource as CatalogSourceBase
from plone.app.z3cform.widget import RelatedItemsFieldWidget
from plone.autoform import directives as form
from plone.supermodel import model
from rer.solrpush import _
from z3c.relationfield.schema import RelationChoice
from z3c.relationfield.schema import RelationList
from zope import schema
from zope.i18n import translate
from zope.interface import Invalid
from zope.interface import invariant
from zope.globalrequest import getRequest

import json


class CatalogSource(CatalogSourceBase):
    """
    Without this hack, validation doesn't pass
    """

    def __contains__(self, value):
        return True  # Always contains to allow lazy handling of removed objs


class IElevateRowSchema(model.Schema):
    text = schema.List(
        title=_("elevate_row_schema_text_label", default=u"Text"),
        description=_(
            "elevate_row_schema_text_help",
            default=u"The word that should match in the search.",
        ),
        required=True,
        value_type=schema.TextLine(),
    )
    uid = RelationList(
        title=_("elevate_row_schema_uid_label", u"Elements"),
        description=_(
            "elevate_row_schema_uid_help",
            u"Select a list of elements to elevate for that search word.",
        ),
        value_type=RelationChoice(vocabulary="plone.app.vocabularies.Catalog"),
        required=True,
    )
    form.widget(
        "uid",
        RelatedItemsFieldWidget,
        vocabulary="plone.app.vocabularies.Catalog",
    )


class IElevateSettings(model.Schema):
    """ """

    elevate_schema = schema.SourceText(
        title=_(u"elevate_schema_label", default=u"Elevate configuration"),
        description=_(
            u"elevate_schema_help",
            default=u"Insert a list of values for elevate.",
        ),
        required=False,
    )

    @invariant
    def elevate_invariant(data):
        schema = json.loads(data.elevate_schema)
        request = getRequest()
        words_mapping = [x["text"] for x in schema]
        for i, schema_item in enumerate(schema):
            elevate_text = schema_item.get("text", [])
            if not elevate_text:
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
            for text in elevate_text:
                for words_i, words in enumerate(words_mapping):
                    if i == words_i:
                        # it's the current config
                        continue
                    if text in words:
                        raise Invalid(
                            translate(
                                _(
                                    "text_duplicated_label",
                                    default='"${text}" is used in several groups.',
                                    mapping=dict(id=i, text=text),
                                ),
                                context=request,
                            )
                        )
