# -*- coding: utf-8 -*-
from datetime import datetime
from DateTime import DateTime
from plone import api
from rer.solrpush.utils.solr_indexer import get_index_fields
from rer.solrpush.utils.solr_indexer import get_site_title
from OFS.Traversable import path2url

try:
    from ZTUtils.Lazy import Lazy
except ImportError:
    from Products.ZCatalog.Lazy import Lazy

timezone = DateTime().timezone()


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

    def getId(self):
        return self.id

    def getPath(self):
        """ convenience alias """

        return self.get("path", "")

    def getObject(self, REQUEST=None, restricted=True):
        if self.is_current_site:
            return api.content.get(self.getPath().encode("utf-8"))
        return self

    def _unrestrictedGetObject(self):
        raise NotImplementedError

    def getURL(self, relative=False):
        """
        If site_name is the current site, convert the physical path into a url, if it was stored.
        Else return url attribute stored in SOLR
        """
        if not self.is_current_site:
            return self.get("url", "")
        path = self.getPath()
        path = path
        try:
            url = self.request.physicalPathToURL(path, relative)
        except AttributeError:
            url = path2url(path.split("/"))
        return url

    def Creator(self):
        return self.get("Creator", "")

    def review_state(self):
        return self.get("review_state", "")

    @property
    def getIcon(self):
        return False

    def PortalType(self):
        return self.get("portal_type", "")

    def EffectiveDate(self):
        return self.get("effective", None)

    def location(self):
        return self.get("location", "")

    def ModificationDate(self):
        value = self.get("ModificationDate", None)
        if not value:
            return None
        return DateTime(value).toZone(timezone)


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
