# -*- coding: utf-8 -*-
from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import directives
from plone.supermodel import model
from rer.solrpush import _
from zope import schema
from zope.interface import provider


@provider(IFormFieldProvider)
class ISolrFields(model.Schema):
    """Additional fields to control Solr integration"""

    directives.fieldset("categorization", fields=["showinsearch", "searchwords"])

    showinsearch = schema.Bool(
        required=False,
        default=True,
        missing_value=True,
        title=_("label_showinsearch", default="Show in search"),
        description=_("help_showinsearch", default=""),
    )

    searchwords = schema.List(
        required=False,
        default=[],
        missing_value=[],
        title=_("label_searchwords", default="Search words"),
        value_type=schema.TextLine(),
        description=_(
            "help_searchwords",
            "Specify words for which this item will show up "
            "as the first search result. Multiple words can be "
            "specified on new lines.",
        ),
    )


# EOF
