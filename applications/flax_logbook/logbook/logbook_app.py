import os
import sys
try:
    import simplejson as json
except ImportError:
    import json
import time
import urllib

import ext

import web
import flax.searchclient
import highlight
import render

FLAX_SERVER = 'http://localhost:8080/'

EM_VIEW = 0
EM_EDIT = 1
EM_NEW = 2

urls = (
    '^/$',                                  'root',
    '^/dbs/(\w+)/docs/(\w+)/edit$',         'doc_edit',
    '^/dbs/(\w+)/docs/(\w+)$',              'doc_view',
    '^/dbs/(\w+)/docs/(\w+)/similar$',      'doc_similar',
    '^/dbs/(\w+)/docs$',                    'docs',
    '^/dbs/(\w+)/new/doc/edit$',            'newdoc_edit',
    '^/dbs/(\w+)/terms/(\w+)$',             'get_terms',
    '^/dbs/(\w+)/fields/(\w+)/getnew$',     'get_newfield',
    '^/dbs/(\w+)/search$',                  'search',
)
    
# FIXME!
naga_schema = {
    'title': '',
    'caption': '',
    'medium': '',
    'location': '',
    'date': '',
    'text': '',
    'person': '',
    'refnext': '',
    'refprev': '',
    'production': [('person', ''), ('date', '')],
    'acquirer': [('person', ''), ('date', '')],
}

NAGA_SCHEMA_FLAT = {                             # FIXME!
    'refnext': 'reference',    
    'refprev': 'reference',
    'text': 'text',
    'caption': 'shorttext', 
    'title': 'shorttext', 
    'person': 'filter', 
    'medium': 'filter', 
    'ethnicgroup': 'filter', 
    'location': 'filter', 
    'date': 'date', 
    'keywords': 'filter', 
    'note': 'note', 
    'form': 'filter', 
    'refnum': 'filter',
    'acquirer': 'group',
    'clip': 'group',
    'collection': 'group',
    'production': 'group',
}


def get_default_field_value(db_name, field_name):
    return naga_schema.get(field_name, '')


class root:
    def GET(self):
        raise web.seeother('/dbs/naga/search')  # FIXME

class doc_edit:
    def GET(self, db_name, doc_id):
        db = flax.searchclient.Client(FLAX_SERVER).db(db_name)
        doc = json.loads(db.get_document(doc_id)['_bamboo_doc'][0])
        return render.doc_edit(db_name, db, NAGA_SCHEMA_FLAT, doc_id, doc)

class newdoc_edit:
    def GET(self, db_name):
        # FIXME
        db = flax.searchclient.Client(FLAX_SERVER).db(db_name)
        doc = [('title', ''), ('text', '')]
        return render.doc_edit(db_name, db, NAGA_SCHEMA_FLAT, None, doc)

class doc_view:
    def GET(self, db_name, doc_id):
        db = flax.searchclient.Client(FLAX_SERVER).db(db_name)
        doc = json.loads(db.get_document(doc_id)['_bamboo_doc'][0])
        return render.doc_view(db_name, db, NAGA_SCHEMA_FLAT, doc_id, doc)

class docs:
    def POST(self, db_name):
        i = web.input(json=None)
        if json:
            bamboo_doc = formdata_to_bamboo_doc(i.json)
            doc_id, fields = flatten(bamboo_doc)
            db = flax.searchclient.Client(FLAX_SERVER).db(db_name)
            db.add_document(fields, doc_id)
            db.flush()  # FIXME?

            web.header('Content-Type:', 'text/javascript')
            return str(db.doccount)

        else:
            raise web.BadRequest

class get_terms:
    def GET(self, db_name, field_name):
        webin = web.input(q='')
        db = flax.searchclient.Client(FLAX_SERVER).db(db_name)
        terms = db.get_terms(field_name, starts_with=webin.q, max_terms=20)
        
        web.header('Content-Type:', 'text/plain')
        return '\n'.join(terms)

class get_newfield:
    def GET(self, db_name, field_name):
        fielddef = get_default_field_value(db_name, field_name)
        return render.new_field([field_name, fielddef], NAGA_SCHEMA_FLAT)

class search:
    def GET(self, db_name):
        webin = web.input(q='', start_rank='0', end_rank='10')
        db = flax.searchclient.Client(FLAX_SERVER).db(db_name)
        results = db.search_simple(webin.q, int(webin.start_rank), int(webin.end_rank))
        return render.search_simple(db_name, db, webin.q, 
            int(webin.start_rank), int(webin.end_rank), results)

class doc_similar:
    def GET(self, db_name, doc_id):
        db = flax.searchclient.Client(FLAX_SERVER).db(db_name)
        results = db.search_similar(doc_id)
        return render.search_similar(db_name, db, doc_id, 0, 10, results)

## utils

def formdata_to_bamboo_doc(data):
    """Convert form data as supplied to docs.POST into a structured Bamboo document.
    
    """
    if isinstance(data, basestring):
        data = json.loads(data)

    top = []
    stack = [top]
    for field in data:
        n = field['name']
        v = field['value']
        if v == '__bam_open_group__':
            v = []
            stack[-1].append([n, v])
            stack.append(v)
        elif v == '__bam_close_group__':
            stack.pop()
        else:
            stack[-1].append([n, v])
            
    return top

def flatten(obj):
    """Flatten for Flax

    """
    doc_id = None
    fields = {}
    obj2 = []
    for o in obj:
        if o[0] == 'id':
            # remove id from the fields and assign to Flax doc_id
            assert isinstance(o[1], basestring)
            doc_id = o[1]
        else:
            obj2.append(o)            
            if isinstance(o[1], basestring):
                fields.setdefault(o[0], []).append(o[1])
            else:
                for o2 in o[1]:
                    fname = '%s/%s' % (o[0], o2[0])
                    fields.setdefault(fname, []).append(o2[1])

    fields['_bamboo_doc'] = json.dumps(obj2)
    return doc_id, fields

def make_app():
    return web.application(urls, globals(), autoreload=True)

