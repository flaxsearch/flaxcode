
# standard modules
import os

class IndexSpec(object):
    """
    Specifies how indexing of a document collection should take place.

    This includes information about both database creation, and (re)-indexing.

    """

    _stopwords = ['i', 'a', 'an', 'and', 'the']


    def update(self, language = "en", stopwords = _stopwords, **kwargs):
        self.language = language
        self.stopwords = stopwords if isinstance(stopwords, list) else stopwords.split(" ")
        self.maybe_make_db()

    def dbname(self):
        raise NotImplementedError, "Subclasses must implement dbname"


    def maybe_make_db(self):
        dbname = self.dbname()
        if not os.path.exists(dbname):
            conn = xappy.IndexerConnection(dbname)
            conn.add_field_action("filename", xappy.FieldActions.INDEX_EXACT)
            conn.add_field_action("filename", xappy.FieldActions.STORE_CONTENT)
            conn.add_field_action('text', xappy.FieldActions.INDEX_FREETEXT, 
                                  language=self.language, stop=self.stopwords, noprefix=True)
            conn.add_field_action('text', xappy.FieldActions.STORE_CONTENT)      
            conn.close()

    
