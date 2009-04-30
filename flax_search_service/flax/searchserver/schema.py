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
        API documentation. This method also validates the field definition, raising
        a FieldError if definition is invalid.

        """

        # check we only have valid keys
        for k in fieldprops.iterkeys():
            if k not in ('type', 'store', 'spelling_source', 'sortable', 
                        'freetext', 'exacttext', 'range', 'geo'):
                raise FieldError, 'invalid field property (%s)' % k

        def validate_attr(key, allowed):
            try:
                if fieldprops[key] not in allowed:
                    raise FieldError, 'invalid value (%s) for field property (%s)' % (fieldprops[key], key)
            except KeyError:
                pass
        
        validate_attr('type', ('text', 'date',))
        validate_attr('store', (True, False))
        validate_attr('spelling_source', (True, False))
        validate_attr('sortable', (True, False))
        validate_attr('exacttext', (True, False))

        if fieldprops.get('freetext') and fieldprops.get('exacttext'):
            raise FieldError, 'cannot have freetext and exacttext specified for same field'

        freetext = fieldprops.get('freetext')
        if freetext:
            if isinstance(freetext, dict):
                for k, v in freetext.iteritems():
                    if k == 'language':
                        if v not in ('da', 'nl', 'en', 'lovins', 'porter', 'fi', 'fr', 
                                     'de', 'it', 'no', 'pt', 'ru', 'es', 'sv',):
                            raise FieldError, 'invalid value for language (%s)' % v
                    elif k == 'term_frequency_multiplier':
                        if (not isinstance(v, int)) or v < 1:
                            raise FieldError, 'invalid value for term_frequency_multiplier (%s)' % v
                    elif k == 'enable_phrase_search':
                        if not v in (True, False):
                            raise FieldError, 'invalid value for enable_phrase_search (%s)' % v
                    else:
                        raise FieldError, 'invalid freetext property (%s)' % k                

            elif freetext not in (True, []):
                raise FieldError, 'invalid value (%s) for freetext' % freetext
            
        # finally accept the field
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
                if freetext is not None:
                    if freetext is True or freetext == []:
                        freetext = {}
                        
                    term_frequency_multiplier = freetext.get('term_frequency_multiplier', 1)
                    enable_phrase_search = freetext.get('enable_phrase_search')

                    language = freetext.get('language')
                    if language is None:
                        indexer_connection.add_field_action(fieldname, 
                            xappy.FieldActions.INDEX_FREETEXT, 
                            weight = term_frequency_multiplier,
                            nopos = not enable_phrase_search)
                    else:
                        indexer_connection.add_field_action(fieldname, 
                            xappy.FieldActions.INDEX_FREETEXT, 
                            weight = term_frequency_multiplier,
                            language = language,
                            nopos = not enable_phrase_search)

                if fieldprops.get('exacttext'):
                    indexer_connection.add_field_action(fieldname,
                        xappy.FieldActions.INDEX_EXACT)

            else:
                raise NotImplementedError
        
            if fieldprops.get('store'):
                indexer_connection.add_field_action(fieldname, 
                    xappy.FieldActions.STORE_CONTENT) 

class FieldError(Exception):
    """Class representing an error in a field definition.
    
    """
    pass