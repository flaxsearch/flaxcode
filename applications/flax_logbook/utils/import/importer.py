import sys
import os
up = os.path.dirname
sys.path.insert(0, os.path.join(up(up(up(os.path.realpath(__file__)))), 'bamboo_webpy'))
print sys.path
import ext

from lxml import etree
try:
    import simplejson as json
except ImportError:
    import json
import flax.searchclient

import naga_schema as bamboo_schema

class FlaxObj:
    def __init__(self):
        self.fields = {}
        self.docid = None
        
def flatten(obj):
    """Flatten for Flax

    """
    fobj = FlaxObj()
    for o in obj:
        if isinstance(o[1], basestring):
            if o[0] == 'id':
                fobj.docid = o[1]
            else:
                fobj.fields.setdefault(o[0], []).append(o[1])
        else:
            for o2 in o[1]:
                fname = '%s/%s' % (o[0], o2[0])
                fobj.fields.setdefault(fname, []).append(o2[1])

    obj2 = [o for o in obj if o[0] != 'id']
    fobj.fields['_bamboo_doc'] = json.dumps(obj2)
    return fobj

def do_import(db, dbname, xmlfile):
    f = open(xmlfile)
    count = 0
    for event, element in etree.iterparse(f):
        if element.tag == 'document':
            obj = []
            for el in element:
                if el.text:
                    # HACK - join text fields
                    if obj and obj[-1][0] == 'text' and el.tag == 'text':
                        obj[-1][1] = '%s\n\n%s' % (obj[-1][1], el.text)
                    else:
                        obj.append([el.tag, el.text])
                else:
                    obj.append([el.tag, [(el2.tag, el2.text) for el2 in el]])

            fobj = flatten(obj)
            print count, fobj.docid
            count += 1

            db.add_document(fobj.fields, docid=fobj.docid)
            if count % 10000 == 0:
                db.flush()

    db.flush()
    f.close()

def get_db(fss, dbname):
    try:
        fss.create_database(dbname)
        schema = fss.schema(dbname)
        for f in bamboo_schema.fields:
            schema.add_field(f[0], f[1])
        
    except flax.searchclient.FlaxError, e:
        assert 'already exists' in str(e)

    return fss.db(dbname)

if __name__ == '__main__':
    fss = flax.searchclient.Client('http://localhost:8080/')
    db = get_db(fss, sys.argv[1])
    do_import(db, sys.argv[1], sys.argv[2])


