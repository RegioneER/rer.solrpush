# -*- coding: utf-8 -*-
from plone.app.vocabularies.catalog import CatalogSource as CatalogSourceBase
from plone.app.z3cform.widget import RelatedItemsFieldWidget
from plone.autoform import directives as form
from plone.supermodel import model
from rer.solrpush import _
from zope import schema


class CatalogSource(CatalogSourceBase):
    """
    Collection tile specific catalog source to allow targeted widget.
    Without this hack, validation doesn't pass
    """

    def __contains__(self, value):
        return True  # Always contains to allow lazy handling of removed objs


class IElevateRowSchema(model.Schema):
    text = schema.TextLine(
        title=_("elevate_row_schema_text_label", default=u"Text"),
        description=_(
            "elevate_row_schema_text_help",
            default=u"The word that should match in the search.",
        ),
        required=True,
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


class IRerSolrpushConf(model.Schema):
    """"""

    active = schema.Bool(
        title=_(u"Active"),
        description=_(u"Enable SOLR indexing on this site."),
        required=False,
        default=False,
    )

    force_commit = schema.Bool(
        title=_(u"Force commit"),
        description=_(
            u"Force commits on CRUD operations. If enabled, each indexing "
            u"operation to SOLR will be immediately committed and persisted. "
            u"This means that updates are immediately available on SOLR queries."  # noqa
            u"If you are using SolrCloud with ZooKeeper, immediate commits "
            u"will slow down response performances when indexing, so it's "
            u"better to turn it off. In this case updates will be available "
            u"when SOLR periodically commit changes."
        ),
        required=False,
        default=True,
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
    # NASCOSTO DAL PANNELLO DI CONTROLLO (vedi: browser/controlpanel.py)
    ready = schema.Bool(
        title=_(u"Ready"),
        description=_(u"SOLR push is ready to be used."),
        required=False,
        default=False,
    )


class IRerSolrpushSearchConf(model.Schema):
    query_debug = schema.Bool(
        title=_(u"Query debug"),
        description=_(
            u"If enabled, when a search to SOLR is performed (for "
            u"example in Collection), the query will be showed in the page for "
            u"debug. Only visible to Managers."
        ),
        required=False,
        default=False,
    )
    remote_elevate_schema = schema.TextLine(
        title=_(u"remote_elevate_label", default=u"Remote elevate"),
        description=_(
            u"remote_elevate_help",
            default=u'If this field is set and no "site_name" is '
            u"passed in query, elevate schema is taken from an external "
            u"source. This is useful if you index several sites and handle "
            u"elevate configuration in one single site. This should be an url "
            u'that points to "@elevate-schema" view.'
            u"For example: http://my-site/@elevate-schema.",
        ),
        default=u"",
        required=False,
    )
    qf = schema.TextLine(
        title=_("qf_label", default=u"qf (query fields)"),
        description=_(
            "qf_help",
            default=u"Set a list of fields, each of which is assigned a boost "
            u"factor to increase or decrease that particular field’s "
            u"importance in the query. "
            u"For example: fieldOne^1000.0 fieldTwo fieldThree^10.0",
        ),
        required=False,
        default=u"",
    )
    bq = schema.TextLine(
        title=_("bq_label", default=u"bq (boost query)"),
        description=_(
            "bq_help",
            default=u"Set a list query clauses that will be added to the main "
            u"query to influence the score. For example if we want to boost "
            u'results that have a specific "searchwords" term: '
            u"searchwords:something^1000",
        ),
        required=False,
        default=u"",
    )

    bf = schema.TextLine(
        title=_("bf_label", default=u"bf (boost functions)"),
        description=_(
            "bf_help",
            default=u"Set a list of functions (with optional boosts) that "
            u"will be used to construct FunctionQueries which will be added "
            u"to the main query as optional clauses that will influence the "
            u"score. Any function supported natively by Solr can be used, "
            u"along with a boost value. "
            u"For example if we want to give less relevance to "
            u"items deeper in the tree we can set something like this: "
            u"recip(path_depth,10,100,1)",
        ),
        required=False,
        default=u"",
    )


class IRerSolrpushSettings(IRerSolrpushConf, IRerSolrpushSearchConf):
    """
    Marker interface for settings
    """
