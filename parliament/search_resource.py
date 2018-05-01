"""
This module contains the metaprogramming needed to extend the
functionality of django-tastypie ``Resource`` class and create new
resource types. For a full description of what this module is, how it
works and why it was created, read:

http://mattdeboard.net/2012/02/07/haystack-resource-for-django-tastypie/

For more information on metaprogramming in Python in general, a good
place to start, and a resource the author referred to frequently while
writing this is "What is a metaclass in Python?":

http://stackoverflow.com/questions/100003/what-is-a-metaclass-in-python

"""

import operator

from django.core.urlresolvers import NoReverseMatch

from haystack.query import SearchQuerySet, SQ

from tastypie import fields
from tastypie.bundle import Bundle
from tastypie.resources import Resource, ResourceOptions, DeclarativeMetaclass
from functools import reduce


class SearchOptions(ResourceOptions):
    # One of the great strengths of Haystack is its extensibility. We have
    # subclassed many of Haystack's internal classes, including a subclass
    # of SearchQuerySet. I did not want to be locked in to using Haystack's
    # built-in SearchQuerySet nor its SQ object in this module, so I put in
    # the ``query_object`` attribute on the metaclass.
    resource_name = 'search'
    object_class = SearchQuerySet
    query_object = SQ
    index_fields = []
    # Override document_uid_field with whatever field in your index
    # you use to uniquely identify a single document. This value will be
    # used wherever the ModelResource references the ``pk`` kwarg.
    document_uid_field = 'id'
    lookup_sep = ','
    

class SearchDeclarativeMetaclass(DeclarativeMetaclass):
    def __new__(cls, name, bases, attrs):
        new_class = super(SearchDeclarativeMetaclass, cls)\
            .__new__(cls, name, bases, attrs)
        opts = getattr(new_class, 'Meta', None)
        new_class._meta = SearchOptions(opts)
        include_fields = getattr(new_class._meta, 'fields', [])
        excludes = getattr(new_class._meta, 'excludes', [])
        field_names = list(new_class.base_fields.keys())
        
        for field_name in field_names:
            if field_name == 'resource_uri':
                continue
            if field_name in new_class.declared_fields:
                continue
            if len(include_fields) and not field_name in include_fields:
                del(new_class.base_fields[field_name])
            if len(excludes) and field_name in excludes:
                del(new_class.base_fields[field_name])

        if getattr(new_class._meta, 'include_absolute_url', True):
            if not 'absolute_url' in new_class.base_fields:
                new_class.base_fields['absolute_url'] = fields.CharField(
                    attribute='get_absolute_url', readonly=True)
        elif 'absolute_url' in new_class.base_fields and not 'absolute_url' in attrs:
            del(new_class.base_fields['absolute_url'])

        return new_class
        

class SearchResource(Resource, metaclass=SearchDeclarativeMetaclass):
    """
    Blueprint for implementing an HTTP API to access documents in a
    search engine via Haystack. The design of the class adds some
    additional configuration overhead (i.e. a handful of metaclass
    fields) in exchange for flexibility & portability.

    To implement this class in your own application, you will need to:
    1. Define which fields to return in your results;
    2. Override index_fields in the metaclass to limit or expand which
       fields consumers can access from your index via the API;
    3. Override document_uid_field in the metaclass to specify which
       field in the index is used to uniquely identify individual
       documents;
    4. Additionally, you will override query_object and object_class to
       utilize any subclasses you may be using in your project.

    """
    
    # Each method in this class definition comes from its parent class. Any
    # unusual or completely new behavior is documented. For documentation
    # on other methods, please refer to the tastypie documentation:
    # http://django-tastypie.readthedocs.org/en/latest/index.html
    def apply_filters(self, request, applicable_filters):
        objects = self.get_object_list(request)

        if applicable_filters:
            return objects.filter(applicable_filters)
        else:
            return objects

    def build_filters(self, filters=None):
        """
        Create a single SQ filter from querystring parameters that
        correspond to SearchIndex fields that have been "registered" in
        the ``self._meta.index_fields``.

        Default behavior is to ``OR`` terms for the same parameter, and
        ``AND`` between parameters. For example:

        ``?format=json&state_exact=Indiana,Illinois&company_exact=IBM``

        would yield an SQ expressing the following logic:

        ``q=state_exact:(Indiana OR Illinois) AND company_exact:IBM``

        Any querystring parameters that are not registered in
        self._meta.index_fields and are not consumed elsewhere in the
        response operation will be ignored.

        """
        terms = []

        if filters is None:
            filters = {}

        for param, value in list(filters.items()):
            
            if param not in self._meta.index_fields:
                continue
                
            tokens = value.split(self._meta.lookup_sep)
            field_queries = []
            
            for token in tokens:
                
                if token:
                    field_queries.append(self._meta.query_object((param,
                                                                  token)))

            terms.append(reduce(operator.or_,
                                [x for x in field_queries if x]))

        if terms:
            return reduce(operator.and_, [x for x in terms if x])
        else:
            return terms
        
    def get_resource_uri(self, bundle_or_obj=None, url_name='api_dispatch_list'):
        if bundle_or_obj is not None:
            url_name = 'api_dispatch_detail'

        try:
            return self._build_reverse_url(url_name, kwargs=self.resource_uri_kwargs(bundle_or_obj))
        except NoReverseMatch:
            return ''

    def get_object_list(self, request):
        """
        A Haystack-specific implementation of ``get_object_list``.

        Returns a SearchQuerySet that may have been limited by other
        filter/narrow/etc. operations.
        
        """
        return self._meta.object_class()._clone()

    def obj_get_list(self, bundle, **kwargs):
        filters = {}
        request = bundle.request
        if hasattr(request, 'GET'):
            filters = request.GET.copy()

        filters.update(kwargs)
        applicable_filters = self.build_filters(filters=filters)
        return self.apply_filters(request, applicable_filters)

    def obj_get(self, request=None, **kwargs):
        """
        Fetch a single document from the datastore according to whatever
        unique identifier is available for that document in the
        SearchIndex.

        """
        # Don't let the use of 'pk' here and throughout confuse you.
        # Think of it as a metaphor standing for "whatever field there
        # is in your SearchIndex that uniquely identifies a single
        # document."
        doc_uid = kwargs.get('pk')
        uid_field = self._meta.document_uid_field
        sqs = self.get_object_list(request)
        
        if doc_uid:
            sqs = sqs.filter(self._meta.query_object((uid_field, doc_uid)))

            if sqs:
                return sqs[0]
            else:
                return sqs
