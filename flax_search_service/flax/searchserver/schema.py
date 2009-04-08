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
r"""Schema (fields, groups, default) stuff for search server.

"""
__docformat__ = "restructuredtext en"

import xappy

class Schema(object):

    def __init__(self, dict_data=None):
        self.fields = {}
        if dict_data:
            self.fields = dict_data['fields']
    
    def as_dict(self):
        return { 'fields': self.fields }

    def set_field(self, fieldname, fieldprops):
        """Set a field from the name and properties supplied.

        Each field is defined as a JSON object with the following items (most of which are optional)::
        
          {
            "type":             # One of "text", "date", "geo", "float" (default=text)
            "store":            # boolean (default=false), whether to store in document data
        
            "spelling_source":  # boolean (default=true), whether to use for building the spelling dictionary
                                # Note - currently, only used if the field is indexed as freetext. FIXME?
                                # May only be specified if type == "text".
        
            "sortable":         # boolean (default=false), whether to allow sorting, collapsing and weighting on the field
                                # Allowed for type == "text", "date", "float" - not for "geo".
        
            "freetext": {       # If present (even if empty) field is indexed for free text searching
                                # Requires type == "text".
                "language":                  # string (2 letter ISO lang code) (default None) - if missing, use
                                             # database default.
                "term_frequency_multiplier": # int (default 1) - must be positive or zero -
                                             # multiplier for term frequency, increases term frequency by the
                                             # given multipler to increase its weighting
                "enable_phrase_search":      # boolean (default True) - whether to allow phrase searches on this field
             },
             "exacttext":       # boolean. If true, search is indexed for exact text searching
                                # Requires type == "text".
                                # Note - only one of "freetext" and "exact" may be supplied
        
             "range" {
                 # details of the acceleration terms to use for range searches.  May only be specified if type == "float" and sortable == true.
                 # FIXME - contents of this hasn't been defined yet - we'll work it out once we have the rest working.
             }
        
             "geo": {
                  # If present (even if empty), coordinates are stored such that searches can be ordered by distance from a point.
                  "enable_bounding_box_search":  # boolean (default=true) - if true, index such that searches for all
                                                 # items within a bounding box can be retrieved.
                  "enable_range_search':  # boolean (default=true) - if true, index such that searches can be
                                          # restricted to all items within a range (ie, great circle distance) of a point.
              }
          }
        
        FIXME - validate field_props
        """        
        self.fields[fieldname] = fieldprops
    
    def get_field(self, fieldname):
        """Return properties for the named field.
        
        """
        return self.fields[fieldname]
        
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
            if fieldtype == 'text':
                freetext = fieldprops.get('freetext')
                if freetext:
                    assert isinstance(freetext, dict)  # FIXME?
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

