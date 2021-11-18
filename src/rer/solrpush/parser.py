# -*- coding: utf-8 -*-
from datetime import datetime
from DateTime import DateTime
from plone import api
from Products.MimetypesRegistry.MimeTypeItem import guess_icon_path
from rer.solrpush.browser.scales import SolrScalesHandler
from rer.solrpush.interfaces.adapter import ISolrBrain
from rer.solrpush.interfaces.settings import IRerSolrpushSettings
from rer.solrpush.utils.solr_indexer import get_index_fields
from rer.solrpush.utils.solr_indexer import get_site_title
from zope.globalrequest import getRequest
from zope.interface import implementer

try:
    from ZTUtils.Lazy import Lazy
except ImportError:
    from Products.ZCatalog.Lazy import Lazy

try:
    from design.plone.theme.interfaces import IDesignPloneThemeLayer

    HAS_RER_THEME = True
except ImportError:
    HAS_RER_THEME = False

import os
import six

timezone = DateTime().timezone()


@implementer(ISolrBrain)
class Brain(dict):
    """ a dictionary with attribute access """

    def __repr__(self):
        return "<SolrBrain for {}>".format(self.getPath())

    def __getattr__(self, name):
        """ look up attributes in dict """
        marker = []
        value = self.get(name, marker)
        schema = get_index_fields()
        if value is not marker:
            field_schema = schema.get(name, {})
            if field_schema.get("type", "") == "date":
                # dates are stored in SOLR as UTC
                value = DateTime(value).toZone(timezone)
            return value
        else:
            if name not in schema:
                raise AttributeError(name)

    def __init__(self, context, request=None):
        self.context = context
        self.request = request
        self.update(context)  # copy data

    @property
    def is_current_site(self):
        return self.get("site_name", "") == get_site_title()

    @property
    def id(self):
        """ convenience alias """
        return self.get("id", self.get("getId"))

    @property
    def Description(self):
        return self.get("description", "")

    @property
    def Date(self):
        if self.EffectiveDate().startswith("1969"):
            return self.CreationDate()
        return self.EffectiveDate()

    def getId(self):
        return self.id

    def getPath(self):
        """ convenience alias """

        return self.get("path", "")

    def getObject(self, REQUEST=None, restricted=True):
        if self.is_current_site:
            path = self.getPath()
            if six.PY2:
                path = path.encode("utf-8")
            return api.content.get(path)
        return self

    def _unrestrictedGetObject(self):
        raise NotImplementedError

    def getURL(self, relative=False):
        """
        If site_name is the current site, convert the physical path into a url, if it was stored.
        Else return url attribute stored in SOLR
        """
        url = self.get("url", "")
        if self.is_current_site:
            frontend_url = api.portal.get_registry_record(
                "frontend_url", interface=IRerSolrpushSettings, default=""
            )
            if frontend_url:
                return url.replace(
                    frontend_url.rstrip("/"), api.portal.get().portal_url()
                )
        return url

    def Creator(self):
        return self.get("Creator", "")

    def review_state(self):
        return self.get("review_state", "")

    def PortalType(self):
        return self.get("portal_type", "")

    def CreationDate(self):
        return self.get("created", None)

    def EffectiveDate(self):
        return self.get("effective", None)

    def location(self):
        return self.get("location", "")

    def ModificationDate(self):
        value = self.get("ModificationDate", None)
        if not value:
            return None
        return DateTime(value).toZone(timezone)

    def MimeTypeIcon(self):
        mime_type = self.get("mime_type", None)
        if not mime_type:
            return ""
        mtt = api.portal.get_tool(name="mimetypes_registry")
        navroot_url = api.portal.get().absolute_url()
        ctype = mtt.lookup(mime_type)
        mimeicon = None
        if not ctype:
            if HAS_RER_THEME:
                if IDesignPloneThemeLayer.providedBy(self.request):
                    mimeicon = os.path.join(
                        navroot_url,
                        "++plone++design.plone.theme/icons/default.svg",
                    )
        else:
            mimeicon = os.path.join(navroot_url, guess_icon_path(ctype[0]))
        return mimeicon

    def restrictedTraverse(self, name):
        if name == "@@images":
            return SolrScalesHandler(self, getRequest())
        return None


class SolrResults(list):
    """ a list of results returned from solr, i.e. sol(a)r flares """


def parseDate(value):
    """use `DateTime` to parse a date, but take care of solr 1.4
    stripping away leading zeros for the year representation"""
    if value.find("-") < 4:
        year, rest = value.split("-", 1)
        value = "%04d-%s" % (int(year), rest)
    return DateTime(value)


def parse_date_as_datetime(value):
    if value.find("-") < 4:
        year, rest = value.split("-", 1)
        value = "%04d-%s" % (int(year), rest)
    format = "%Y-%m-%dT%H:%M:%S"
    if "." in value:
        format += ".%fZ"
    else:
        format += "Z"
    return datetime.strptime(value, format)


class SolrResponse(Lazy):
    """ a solr search response; TODO: this should get an interface!! """

    __allow_access_to_unprotected_subobjects__ = True

    def __init__(self, data=None):
        if getattr(data, "hits", None) is None and data.get("error", False):
            self.actual_result_count = 0
            self._data = {}
        else:
            self.actual_result_count = data.hits
            self._data = data.docs

    def results(self):
        return list(map(Brain, self._data))

    def __getitem__(self, index):
        return self.results()[index]
