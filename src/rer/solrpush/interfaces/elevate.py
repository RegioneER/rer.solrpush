# -*- coding: utf-8 -*-
from collective.z3cform.datagridfield.registry import DictRow
from plone.app.vocabularies.catalog import CatalogSource as CatalogSourceBase
from plone.app.z3cform.widget import RelatedItemsFieldWidget
from plone.autoform import directives as form
from plone.supermodel import model
from rer.solrpush import _
from zope import schema


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
    uid = schema.List(
        title=_("elevate_row_schema_uid_label", u"Elements"),
        description=_(
            "elevate_row_schema_uid_help",
            u"Select a list of elements to elevate for that search word.",
        ),
        value_type=schema.Choice(source=CatalogSource()),
        required=True,
    )
    form.widget("uid", RelatedItemsFieldWidget)


class IElevateSettings(model.Schema):
    """
    """

    elevate_schema = schema.List(
        title=_(u"elevate_schema_label", default=u"Elevate configuration"),
        description=_(
            u"elevate_schema_help",
            default=u"Insert a list of values for elevate.",
        ),
        required=False,
        value_type=DictRow(title=u"elevate row", schema=IElevateRowSchema),
    )
