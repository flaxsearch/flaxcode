# Copyright (c) 2009 Lemur Consulting Ltd
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
r"""Schema (fields, groups, default) support for search server.

"""
__docformat__ = "restructuredtext en"

import xappy

class Schema(object):

    def __init__(self, dict_data=None):
        self.language = 'none'
        self.fields = {}
        self.groups = {}

        if dict_data:
            self.language = dict_data.get('language', self.language)
            self.fields = dict_data.get('fields', self.fields)
            self.groups = dict_data.get('groups', self.groups)
    
    def as_dict(self):
        return {
            'language': self.language,
            'fields': self.fields,
            'groups': self.groups,
        }

    def set_field(self, fieldname, fieldprops):
        """Set a field from the name and properties supplied.

        Each field's schema is represented by a dictionary, as specified in the
        API documentation.

        """        
        self.fields[fieldname] = fieldprops
    
    def get_field(self, fieldname):
        """Return properties for the named field.
        
        """
        return self.fields[fieldname]

    def delete_field(self, fieldname):
        """Remove the named field from the schema.
        
        """
        del self.fields[fieldname]
        
    def get_field_names(self):
        """Return a list of field names.
        
        """
        return self.fields.keys()

    def set_xappy_field_actions(self, indexer_connection):
        """Set the appropriate Xappy field actions to implement our schema.
        
        """        
        for fieldname, fieldprops in self.fields.iteritems():
            fieldtype = fieldprops.get('type', 'text')
            assert fieldtype in ('text', 'date', 'geo', 'float')  # FIXME?
            
            indexer_connection.clear_field_actions(fieldname)
            
            if fieldtype == 'text':
                freetext = fieldprops.get('freetext')
                if freetext:
                    if freetext is True:
                        freetext = {}
                        
                    language = freetext.get('language')
                    term_frequency_multiplier = freetext.get('term_frequency_multiplier', 1)
                    enable_phrase_search = freetext.get('enable_phrase_search')
                    indexer_connection.add_field_action(fieldname, 
                        xappy.FieldActions.INDEX_FREETEXT, 
                        weight = term_frequency_multiplier,
                        language = language,
                        nopos = not enable_phrase_search)
            else:
                raise NotImplementedError
        
            if fieldprops.get('store'):
                indexer_connection.add_field_action(fieldname, 
                    xappy.FieldActions.STORE_CONTENT) 

