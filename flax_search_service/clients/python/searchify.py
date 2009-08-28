# $Id$
# FIXME this needs a name
#

# Note that much of the time, something that's a singleton (eg: a string) can also be an iterable. Where this isn't the case, it probably should be.

# Add an inner class Searchable to your model, with fields (list of django_fields) and cascades (list of strings which are Django fields that are relations to other Django model instances, or callables which return model instances or an iterable thereof).
# Note that you can't have one search field multiple times (only the last one processed will be preserved).
#
# django_field is either a string (name of Django model field, use all defaults), or a dictionary.
# Within the dictionary, ``django_fields`` is either a string (again), or a callable (takes the instance, returns a list of data to index into the search field).
# ``field_name`` is the search field name (optional, auto-generated), ``config`` is an optional dictionary of configuration options (search provider dependent; currently we use xappyc)
# In your search field names, don't start with an underscore ('_') as that's reserved.
#
# We STRONGLY recommend explicitly declaring your search field names, as it makes the resultant search system more useful to users. In some cases you don't need it, but that's rare.
#
# Note that strictly you can have a callable as a django_field directly. In this case, it will be called with a parameter of None to generate the search field name (well, part of it - it only needs to be unique to the class). But don't do this, it's ugly.
#
# In normal use, you may have a single static method in your Searchable inner class, to constrain cascading in complex cases:
#
# reindex_on_cascade(sender, instance) -- defaults to True; ``sender`` is what we've just indexed which cascaded to this ``instance`` of the model
#
# If you really need, you can override most aspects of the data gathering and field generation. Generally speaking you won't have to touch this at all.
#
# get_configuration(model) -- ``model`` is fully constructed and registered, return a list of search field descriptors
# get_field_input(instance, django_field) -- return an iterable, but you almost never want to do this
# get_details(field_descriptor) -- the Searchify field descriptor, returns a tuple (django_field_list, search field name, config dictionary), you almost never want to do this either
#   (importantly, 'field_name' in the dictionary is filled out to the explicit or auto-generated search field name)
# get_index_data(instance) -- return a unique identifier (we use model '.' pk), and a dict of search field names mapping to lists of input data. We auto-create a field _TYPE which is the model name.
#
# EXAMPLE
#
# from django.db import models
#
# class Sea(models.Model):
#   name = models.CharField(null=True, blank=True, max_length=100)
#
#   class Searchable:
#     fields = [ { 'field_name': 'name', 'django_fields': ['name', lambda inst: [n.name for n in inst.narwhals], ] } ]
#
# class Narwhal(models.Model):
#   name = models.CharField(null=True, blank=True, max_length=100)
#   home = models.ForeignKey(Sea, related_name='narwhals')
#
#   class Searchable:
#     fields = [ { 'field_name': 'name', 'django_fields': ['name'] } ]
#     cascades = [ 'home' ]
#
# NASTY DETAILS
#
# When auto-generating, we use '.' to separate bits of things where possible, and '__' where we require \w only.

# FIXME: 'cheap' reindexing of a model (currently we drop the index, which is wrong; we should use the _TYPE discriminating terms)
# FIXME: make it easy to reindex all models
# FIXME: document the query() method added to managers
# FIXME: make query() do pagination properly, on top of anything Flax chooses to offer us (currently Flax gives us nothing)
# FIXME: registering and initialising so we're not bound to Djape. (Possibly even write something to tie into Lucene/Solr or similar.)
# FIXME: other FIXMEs ;-)

# FIXME: drop xapian_index
# FIXME: turn into a proper class-based system rather than this abomination
# FIXME: document all the hooks properly
# FIXME: document that you have to call initialise (and figure out where additional config comes from...). This may change to an admin-style register.

# TODO: make it possible to index an individual model to more than one database.
# TODO: reverse cascades, so you can put searchable stuff into your Profile model, but have it index stuff from the User.
# TODO: if you change the django_fields, searchify should "want" to reindex, with suitable options to tell it not to (how?)
# Test: the override stuff

from django.db.models.signals import post_save, pre_delete, post_delete
from django.db import models
from django.db.models import FieldDoesNotExist, BooleanField
from django.conf import settings
from flax.searchclient import Client, FlaxError
import urlparse

class TestClient:
    def newdb(self, fields, dbname):
        print 'init ' + dbname
        print 'config ' + str(fields)
        
    class Document:
        def __init__(self):
            self.d = {}
            self.id = None
            
        def extend(self, data):
            self.d.update(data)
        
    def add(self, doc):
        print 'index %s: %s' % (doc.id, str(doc.d))
        
    def delete(self, uid):
        print 'delete ' + uid

def get_client(dbname_or_model):
    if not isinstance(dbname_or_model, str):
        dbname = get_index(dbname_or_model)
    else:
        dbname = dbname_or_model

    class MyClient:
        Error = FlaxError
        def __init__(self, url, dbname):
            self.client = Client(url)
            self.dbname = settings.FLAX_PERSONAL_PREFIX + dbname

        def create(self, fields, reopen=False, overwrite=False):
            self.client.create_database(self.dbname, reopen=reopen, overwrite=overwrite)
            schema = self.schema()
            for f,c in fields.items():
                schema.add_field(f, c)
            
        def schema(self):
            return self.client.schema(self.dbname)
            
        def add(self, doc, docid=None):
            db = self.client.db(self.dbname)
            ret = db.add_document(doc, docid)
            db.flush()
            return ret
            
        def search(self, query, query_filter=None, start=0, end=10):
            if filter:
                return self.client.db(self.dbname).search_structured(query_any=query, filter=query_filter, start_rank=start, end_rank=end)
            else:
                return self.client.db(self.dbname).search_simple(query, start, end)
            
        def delete(self, uid):
            db = self.client.db(self.dbname)
            ret = db.delete_document(uid)
            db.flush()
            return ret
        
    return MyClient(
        settings.FLAX_BASE_URL,
        dbname
    )

def make_searcher(manager, model):
    index = get_index(model)
    if not index:
        return None

    client = get_client(index)
    def search(query=None, start=None, end=None, query_filter=None):
        if start==None and end==None:
            # new-style interface. Return an object which responds to slicing and is iterable.
            class SearchResultSet:
                def __init__(self, query, query_filter=None):
                    self.query = query
                    self.query_filter = query_filter
                    self.position = None
                    self.smallest_page = 10
                    # the following are filled out as needed
                    self._results = None # just the current page of results (but contains useful metadata also)
                    self.results = {} # store of index -> decorated Django instance

                def __repr__(self):
                    return "<you ain't got a hope>"

                def __getattr__(self, key):
                    print "__getattr__(%s)" % key
                    """Provide .-access to aspects of the result. eg: q.doc_count (providing the search provider returns doc_count)."""
                    self._ensure_results()
                    return getattr(self._results, key)
                    
                def _ensure_results(self, start=None, end=None):
                    print "_ensure_results(%s,%s)" % (start, end)
                    """
                    Call this before any operation to ensure that we've got some useful results available.
                    If called with start=None, then ensure that the result at self.position is available.
                    If not, ensure that the result at [start] or results at [start:end] are available.
                    """
                    if start==None:
                        start=0
                    if end==None:
                        end=start+1
                    # now reduce [start:end] to the single smallest range that we don't already have
                    while self.results.has_key(start) and start < end:
                        start += 1
                    while self.results.has_key(end) and start < end:
                        end -= 1
                    if start==end:
                        # we have everything we need already
                        return
                    if end-start < self.smallest_page:
                        end = start + self.smallest_page
                    
                    self._results = client.search(self.query, self.query_filter, start, end)
                    result_ids = []
                    match_details = {}
                    for item in self._results.results:
                        search_id = item.docid
                        database_name, model_key, django_id = search_id.split('.')
                        if model_key != model.__name__:
                            # FIXME: not right!
                            # Either we need to get this right, or we could filter the query through a boolean to restrict to
                            # this model in the first place. The latter would work better, but requires some thought. (In particular,
                            # semi-constructing queries like this unsettles Richard, so there's probably a reason to avoid it.)
                            #continue
                            pass
                        result_ids.append(long(django_id))
                        match_details[django_id] = item
                    bulk = manager.in_bulk(result_ids)

                    for key, obj in bulk.items():
                        # From Flax we get: data (dict of field->data pairs), id, rank
                        # We only really care about rank at this stage, as we've pulled out the object.
                        if hasattr(model.Searchable, 'match_details_attribute'):
                            match_attr = model.Searchable.match_details_attribute
                        else:
                            match_attr = 'match'
                        if match_attr is not None:
                            setattr(obj, match_attr, match_details[str(obj.pk)])
                        self.results[start] = obj
                        start += 1
                
                def __iter__(self):
                    return self
                    
                def next(self):
                    print "next()"
                    self._ensure_results()
                    ret = self[self.position]
                    self.position += 1
                    return ret
                    
                def __len__(self):
                    print "__len__()"
                    self._ensure_results()
                    # this is perhaps not the ideal solution, but should work in general
                    return self.matches_upper_bound
                    
                def __getslice__(self, start, end):
                    print "__getslice__(%s, %s)" % (start, end)
                    self._ensure_results(start, end)
                    ret = []
                    try:
                        for idx in range(start, end):
                            ret.append(self.results[idx])
                    except KeyError:
                        # Slices fail silently
                        pass
                    return ret
                    
                def __getitem__(self, index):
                    print "__getitem__(%s)" % index
                    self._ensure_results(index)
                    try:
                        return self.results[index]
                    except KeyError:
                        # Indexing fails noisily
                        raise IndexError('list index out of range')
            
            return SearchResultSet(query, query_filter)
        else:
            # old-style interface
            if start==None:
                start=0
            if end==None:
                end=10
        class QueryResult:
            def __init__(self, results):
                self.results = results
                search_ids = [ item.docid for item in results.results ]
                self._result_ids = []
                self._deets = {}
                for item in results.results:
                    search_id = item.docid
                    database_name, model_key, id = search_id.split('.')
                    if model_key != model.__name__:
                        # FIXME: not right!
                        pass
                    self._result_ids.append(long(id))
                    self._deets[id] = item
                self._bulk = manager.in_bulk(self._result_ids)

            # From Flax, we get: matches_lower_bound, matches_upper_bound, more_matches, matches_estimated, matches_human_readable_estimate
            def __getattr__(self, key):
                """Provide .-access to aspects of the result. eg: q.doc_count (providing the search provider returns doc_count)."""
                return getattr(self.results, key)

            def __len__(self):
                return len(self._result_ids)
            
            def __iter__(self):
                """
                Iterate over the results, in the order they were in the result set.
                Return a decorated object, ie the Django model instance with an extra attribute (default 'match') containing match details (you mostly care about .rank, if provided).
                """
                for key in self._result_ids:
                    obj = self._bulk[long(key)]
                    # From Flax we get: data (dict of field->data pairs), id, rank
                    # We only really care about rank at this stage, as we've pulled out the object.
                    if hasattr(model.Searchable, 'match_details_attribute'):
                        match_attr = model.Searchable.match_details_attribute
                    else:
                        match_attr = 'match'
                    if match_attr is not None:
                        setattr(obj, match_attr, self._deets[str(obj.pk)])
                    yield obj
        
        results = client.search(query, query_filter, start, end)
        return QueryResult(results)
    return search

def get_index(model_or_inst):
    index = None
    if hasattr(model_or_inst.Searchable, 'index'):
        index = getattr(model_or_inst.Searchable, 'index')
    elif hasattr(model_or_inst.Searchable, 'xapian_index'):
        index = getattr(model_or_inst.Searchable, 'xapian_index')
    # The following is not true: you may want to configure aspects of searchify on a non-indexed class (eg: cascades)
    #assert index, 'Searchable classes require an index property (or xapian_index for temporary bc)'
    return index

def initialise():
    indexes = {} # Map Xapian dbname => list of fields
    imodels = []
    for model in models.get_models():
        if not hasattr(model, 'Searchable'):
            continue
        index = get_index(model)
        if index!=None:
            indexes.setdefault(index, {}).update(get_configuration(model))
            imodels.append(model)
    
    # Now loop through and ensure each db exists
    for index, fields in indexes.items():
        if len(fields) == 0:
            continue # Skip this index
        client = get_client(index)
        try:
            client.create(fields, reopen = True)
        except client.Error:
            print "Clearing database '%s' - you will need to re-index" % index
            client.create(fields, overwrite=True)
            raise
    
    # Finally, go back over the models adding searchers to the default manager
    for model in imodels:
        if hasattr(model.Searchable, 'managers'):
            managers = getattr(model.Searchable, 'managers')
        else:
            managers = ['objects']
        for manager in managers:
            manager = getattr(model, manager)
            if hasattr(model.Searchable, 'query'):
                searcher = getattr(model.Searchable, 'query')
            else:
                searcher = make_searcher(manager, model)
            if searcher!=None:
                manager.query = searcher
    
    # Set up the global signal hooks
    post_save.connect(index_hook)
    pre_delete.connect(delete_hook)

def index_hook(sender, **kwargs):
    index_instance(kwargs['instance'])

def delete_hook(sender, **kwargs):
    delete_instance(kwargs['instance'])

def post_delete_hook(instance):
    def hook(sender, **kwargs):
        if kwargs['instance']==instance:
            cascade_reindex(kwargs['instance'])
            post_delete.disconnect(hook)
    return hook

def clear_index(model):
    """Clear the index for a model by (implicitly) deleting and (explicitly) recreating the database."""
    client = get_client(model)
    client.create(get_configuration(model), overwrite=True)

def reindex(model):
    if not hasattr(model, 'Searchable'):
        pass
    clear_index(model) # FIXME: this isn't necessarily right, because multiple models may feed into this index
    # Instead, we could use a discriminating term (which we probably want anyway)
    for inst in model.objects.all():
        print "Reindexing %s" % inst
        index_instance(inst)

def index_instance(instance):
    if not hasattr(instance, 'Searchable'):
        return False

    index = get_index(instance)
    if not index:
        # just cascade if we're not indexing this model directly
        cascade_reindex(instance)
        return
    client = get_client(index)
    
    # next, check should_delete_instance for situations where we *mark* as
    # deleted rather than deleting in the ORM/database
    # (eg: a deleted boolean field)
    if should_delete_instance(instance):
        client.delete(get_uid(instance))
    else:
        dret = get_index_data(instance)
        if dret!=None:
            (ident, fielddata) = dret
            client.add(fielddata, docid=ident)

    cascade_reindex(instance)

def cascade_reindex(instance):
    if not hasattr(instance, 'Searchable') or \
        not hasattr(instance.Searchable, 'cascades'):
        return
    for descriptor in instance.Searchable.cascades:
        cascade_inst = None
        # find the instance we're being told to cascade the reindex onto
        if callable(descriptor):
            cascade_inst = descriptor(instance)
        elif isinstance(descriptor, str):
            cascade_inst = getattr(instance, descriptor)
        # if we found one, check if it's Searchable, check if it wants to accept
        # the cascade, and if so, reindex it
        if cascade_inst:
            # If it's not an iterable already, make it into one
            if not hasattr(cascade_inst, '__iter__'):
                cascade_insts = [cascade_inst]
            else:
                cascade_insts = cascade_inst
            for cascade_inst in cascade_insts:
                if hasattr(cascade_inst, 'Searchable'):
                    if hasattr(cascade_inst.Searchable, 'reindex_on_cascade'):
                        if not cascade_inst.Searchable.reindex_on_cascade(instance, cascade_inst):
                            continue
                    index_instance(cascade_inst)

def delete_instance(instance):
    if hasattr(instance, 'Searchable'):
        index = get_index(instance)
        if index:
            client = get_client(index)
            client.delete(get_uid(instance))
    post_delete.connect(post_delete_hook(instance))

# UTILITY FUNCTIONS
#
# These are the default behaviours for the various steps in the above strategy (some are actually defaults for steps in strategies in functions below).

# Should we delete this instance? By default, we look for a BooleanField called ``deleted``.
# Can be overridden.
def should_delete_instance(instance):
    if not hasattr(instance, 'Searchable'):
        return False
    if hasattr(instance.Searchable, 'should_delete_instance'):
        return instance.Searchable.should_delete_instance(instance)
    try:
        fielddef = instance._meta.get_field('deleted')
        if isinstance(fielddef, BooleanField):
            return instance.deleted
    except FieldDoesNotExist:
        return False

# Get the configuration for a particular model by pulling in details from Searchable.fields
# Can be overridden.
def get_configuration(model):
    # return a map of xappy field names to xappy field configuration
    if not hasattr(model, 'Searchable'):
        return []
    if hasattr(model.Searchable, 'get_configuration'):
        return model.Searchable.get_configuration(model)
    if not hasattr(model.Searchable, 'fields'):
        return []
    fields = {}
    for field in model.Searchable.fields:
        default_config = get_default_configuration(model)
        (django_field_list, search_fieldname, config) = get_details(model, field)
        default_config.update(config)
        fields[search_fieldname] = default_config
    #print "Configuration = %s" % (fields,)
    return fields

# Get the default configuration for a particular model by pulling in details from Searchable.defaults
# Can be overridden. Has sane defaults if there are none.
def get_default_configuration(model):
    if hasattr(model, 'Searchable') and hasattr(model.Searchable, 'defaults'):
        return model.Searchable.defaults
    return { 'type': 'text', 'store': True, 'freetext': {} }

# Return (django_field_list, search field name, config) for a particular search field (which is a string, dict or possibly callable).
# Performs auto-generation of search field names.
# Can be over-ridden.
def get_details(instance_or_model, field):
    if hasattr(instance_or_model, 'Searchable') and hasattr(instance_or_model.Searchable, 'get_details'):
        return instance_or_model.Searchable.get_details(field)
    if type(field) is dict:
        django_field_list = field['django_fields']
        xappy_fieldname = field.get('field_name')
    else:
        django_field_list = [field]
        xappy_fieldname = None
    if xappy_fieldname == None:
        if isinstance(django_field_list[0], str):
            field_specific_name = django_field_list[0]
        elif callable(django_field_list[0]):
            field_specific_name = django_field_list[0](None)
        xappy_fieldname = filter(lambda x: x.isalpha(), field_specific_name)
    # auto-detect index type (eg: date) based on field type (if FIXME: django_field_list allows us to figure it out?)
    if type(field) is dict:
        return (django_field_list, xappy_fieldname, field.get('config', {}))
    else:
        return (django_field_list, xappy_fieldname, {})

# Given a single Django field descriptor (string or callable), generate a list of data to input to the search field.
# Can be overridden.
def get_field_input(instance, django_field):
    #print 'get_field_input ' + str(instance) + ', ' + django_field
    if hasattr(instance, 'Searchable') and hasattr(instance.Searchable, 'get_field_input'):
        return instance.Searchable.get_field_input(instance, django_field)
    # must return an iterable; django_field is str (name) or callable
    if isinstance(django_field, str):
        #print 'trying as str'
        #print '.name = %s' % instance.name
        #print 'getattr(,"name") = %s' % getattr(instance, 'name')
        val = getattr(instance, django_field)

        def datetime_converter(d):
            return unicode(d.date())

        converters = { models.DateTimeField: datetime_converter }
        field = instance._meta.get_field(django_field).__class__
        if val == None:
            return []
        if field in converters:
            val = converters[field](val)
        else:
            val = unicode(val)
        return [val]
    elif callable(django_field):
        return django_field(instance)
    else:
        return []

# Generate a system-wide persistent uid for this instance.
# Can be overridden.
def get_uid(instance):
    if not hasattr(instance,'Searchable'):
        return None
    if hasattr(instance.Searchable, 'get_uid'):
        return instance.Searchable.get_uid(instance)
    else:
        return '%s.%s.%s' % (
            instance._meta.app_label, instance._meta.object_name, instance.pk
        )

# Given a Django model instance, return a unique identifier and a dict of search fields mapping to list of data.
# Can be overridden.
def get_index_data(instance):
    if not hasattr(instance,'Searchable'):
        return None
    if hasattr(instance.Searchable, 'get_index_data'):
        return instance.Searchable.get_index_data(instance)
    if not hasattr(instance.Searchable, 'fields'):
        return None
    fields = instance.Searchable.fields
    
    # ``_TYPE`` field based on model name (so we can search just a particular model)
    outfields = { '_TYPE': [instance._meta.module_name] }
        
    for field in fields:
        (django_field_list, xappy_fieldname, xappy_config) = get_details(instance, field)
        interim_data = map(lambda x: get_field_input(instance, x), django_field_list)
        #print '>>>' + str(interim_data)
        outfields[xappy_fieldname] = reduce(lambda x,y: x + y, interim_data)
    
    return (get_uid(instance), outfields)
