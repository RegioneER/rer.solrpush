# -*- coding: utf-8 -*-
from plone.app.vocabularies.catalog import CatalogSource as CatalogSourceBase
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


class IRerSolrpushConf(model.Schema):
    """"""

    active = schema.Bool(
        title=_("Active"),
        description=_("Enable SOLR indexing on this site."),
        required=False,
        default=False,
    )
    search_enabled = schema.Bool(
        title=_("Search enabled"),
        description=_("Site search will use SOLR as engine instead portal_catalog."),
        required=False,
        default=True,
    )
    force_commit = schema.Bool(
        title=_("Force commit"),
        description=_(
            "Force commits on CRUD operations. If enabled, each indexing "
            "operation to SOLR will be immediately committed and persisted. "
            "This means that updates are immediately available on SOLR queries."  # noqa
            "If you are using SolrCloud with ZooKeeper, immediate commits "
            "will slow down response performances when indexing, so it's "
            "better to turn it off. In this case updates will be available "
            "when SOLR periodically commit changes."
        ),
        required=False,
        default=True,
    )

    solr_url = schema.TextLine(
        title=_("SOLR url"),
        description=_("The SOLR core to connect to."),
        required=True,
    )

    frontend_url = schema.TextLine(
        title=_("Frontend url"),
        description=_("If the website has different URL for frontend users."),
        required=False,
    )

    enabled_types = schema.List(
        title=_("enabled_types_label", default="Enabled portal types"),
        description=_(
            "enabled_types_help",
            default="Select a list of portal types to index in solr. "
            "Empty list means that all portal types will be indexed.",
        ),
        required=False,
        default=[],
        missing_value=[],
        value_type=schema.Choice(vocabulary="plone.app.vocabularies.PortalTypes"),
    )

    index_fields = schema.SourceText(
        title=_(
            "index_fields_label",
            default="List of fields loaded from SOLR that we use for " "indexing.",
        ),
        description=_(
            "index_fields_help",
            default="We store this list for performance"
            " reasons. If the configuration changes, you need to click on"
            " Reload button",
        ),
        required=False,
    )
    # NASCOSTO DAL PANNELLO DI CONTROLLO (vedi: browser/controlpanel.py)
    ready = schema.Bool(
        title=_("Ready"),
        description=_("SOLR push is ready to be used."),
        required=False,
        default=False,
    )


class IRerSolrpushSearchConf(model.Schema):
    query_debug = schema.Bool(
        title=_("Query debug"),
        description=_(
            "If enabled, when a search to SOLR is performed (for "
            "example in Collection), the query will be showed in the page for "
            "debug. Only visible to Managers."
        ),
        required=False,
        default=False,
    )
    remote_elevate_schema = schema.TextLine(
        title=_("remote_elevate_label", default="Remote elevate"),
        description=_(
            "remote_elevate_help",
            default='If this field is set and no "site_name" is '
            "passed in query, elevate schema is taken from an external "
            "source. This is useful if you index several sites and handle "
            "elevate configuration in one single site. This should be an url "
            'that points to "@elevate-schema" view.'
            "For example: http://my-site/@elevate-schema.",
        ),
        default="",
        required=False,
    )
    qf = schema.TextLine(
        title=_("qf_label", default="qf (query fields)"),
        description=_(
            "qf_help",
            default="Set a list of fields, each of which is assigned a boost "
            "factor to increase or decrease that particular field’s "
            "importance in the query. "
            "For example: fieldOne^1000.0 fieldTwo fieldThree^10.0",
        ),
        required=False,
        default="",
    )
    bq = schema.TextLine(
        title=_("bq_label", default="bq (boost query)"),
        description=_(
            "bq_help",
            default="Set a list query clauses that will be added to the main "
            "query to influence the score.",
        ),
        required=False,
        default="",
    )

    bf = schema.TextLine(
        title=_("bf_label", default="bf (boost functions)"),
        description=_(
            "bf_help",
            default="Set a list of functions (with optional boosts) that "
            "will be used to construct FunctionQueries which will be added "
            "to the main query as optional clauses that will influence the "
            "score. Any function supported natively by Solr can be used, "
            "along with a boost value. "
            "For example if we want to give less relevance to "
            "items deeper in the tree we can set something like this: "
            "recip(path_depth,10,100,1)",
        ),
        required=False,
        default="",
    )


class IRerSolrpushSettings(IRerSolrpushConf, IRerSolrpushSearchConf):
    """
    Marker interface for settings
    """
