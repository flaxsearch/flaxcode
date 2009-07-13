import os.path
import urllib
try:
    import simplejson as json
except ImportError:
    import json

from genshi.template import TemplateLoader
from genshi.core import Markup
import highlight

# FIXME: allow DB-specific templates to override standard ones

loader = TemplateLoader(
    os.path.join(os.path.dirname(__file__), '../templates'),
    auto_reload=True
)

print '-- render:', __file__

def doc_edit(db_name, db, schema, doc_id, doc):
    """Render a Bamboo document for editing.
    
    """
    t = loader.load('doc_edit.html')
    s = t.generate(
        db_name=db_name,
        doccount=db.doccount,
        schema=schema,
        title='Edit %s document' % db_name.capitalize(),
        doc_id=doc_id,
        doc=doc,
    )
    return s.render('html', doctype='html')

def doc_view(db_name, db, schema, doc_id, doc):
    """Render a Bamboo document for viewing.
    
    """
    t = loader.load('doc_view.html')
    s = t.generate(
        db_name=db_name,
        doccount=db.doccount,
        schema=schema,
        title='%s document' % db_name.capitalize(), 
        doc_id=doc_id,
        doc=doc,
        format_value=lambda x: Markup(x.replace('\n\n', '<br/>')),
    )
    return s.render('html', doctype='html')

def new_field(fielddef, schema):    
    """Render a single field editor.
    
    """
    t = loader.load('fields.html')
    s = t.generate(doc=None, field=fielddef, schema=schema)
    return s.render('html', doctype=None)
 
def search_simple(db_name, db, q, start_rank, end_rank, results):
    """Render a simple search page.
    
    """
    t = loader.load('search_simple.html')
    info = ''
    if q:
        if results.matches_lower_bound:
            info = '%d to %d of about %d results' % (results.start_rank + 1,
                results.end_rank, results.matches_human_readable_estimate)
        else:
            info = 'No matching documents'
    
    s = t.generate(
        search_type='simple',
        db_name=db_name,
        doccount=db.doccount,
        q=q,
        info=info,
        start_rank=start_rank,
        end_rank=end_rank,
        hits=(Hit(db_name, result, q) for result in results.results),
        title='Search %s database' % db_name.capitalize()
    )
    return s.render('html', doctype='html')

def search_similar(db_name, db, doc_id, start_rank, end_rank, results):
    """Render a simple search page.
    
    """
    t = loader.load('search_simple.html')
    if results.matches_lower_bound:
        info = '%d to %d of about %d results' % (results.start_rank + 1,
            results.end_rank, results.matches_human_readable_estimate)
    else:
        info = 'No matching documents'
    
    s = t.generate(
        search_type='similar',
        db_name=db_name,
        doccount=db.doccount,
        doc_id=doc_id,
        info=info,
        start_rank=start_rank,
        end_rank=end_rank,
        hits=(Hit(db_name, result, None) for result in results.results),
        title='Search %s database' % db_name.capitalize()
    )
    return s.render('html', doctype='html')

class Hit(object):
    def __init__(self, db_name, result, q):
        """Generate information for display in a search result. 

        """
        self.rank = result.rank + 1
        data = json.loads(result.data['_bamboo_doc'][0])
        text = []
        self.caption = ''

        for field in data:
            if field[0] == 'title' and not self.caption:       # HACK
                self.caption = field[1]
            elif field[0] == 'text':
                text.append(field[1])

        text = ' '.join(text)
        
        # generate a summary
        if q:
            hl = highlight.Highlighter()
            qterms = [(x,) for x in q.split()]
            self.sample = Markup(hl.makeSample(text, qterms, 400, hl=('<b>', '</b>')))
        elif len(text) > 400:
            self.sample = text[:400] + '...'
        else:
            self.sample = text
            
        docurl = '/dbs/%s/docs/%s' % (urllib.quote_plus(db_name), 
            urllib.quote_plus(result.docid))
            
        self.view_href = docurl
        self.edit_href = docurl + '/edit'
        self.similar_href = docurl + '/similar'


