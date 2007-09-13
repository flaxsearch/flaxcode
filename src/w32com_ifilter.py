#$Id : xxx $
import itertools
import pythoncom
import pywintypes
from win32com.ifilter import ifilter
from win32com.ifilter.ifiltercon import *


prop_id_map = { 19 : "Text",
                 3 : "HtmlHeading1" }


def prop_id_to_name(prop_id):
    if type(prop_id) is str:
        return prop_id
    elif prop_id in prop_id_map:
        return prop_id_map[prop_id]
    else:
        return prop_id

def text_for_current_chunk(f):
    
    def get_text():
        try:
            yield f.GetText()
        except pythoncom.com_error, e:
            if e[0] == FILTER_E_NO_MORE_TEXT:
                raise StopIteration
            else:
                raise

    return(''.join(get_text()))

_filter_init_flags = IFILTER_INIT_INDEXING_ONLY | 
                     IFILTER_INIT_APPLY_INDEX_ATTRIBUTES | 
                     IFILTER_INIT_APPLY_CRAWL_ATTRIBUTES| 
                     IFILTER_INIT_APPLY_OTHER_ATTRIBUTES | 
                     IFILTER_INIT_SEARCH_LINKS

def ifilter_filter(filename, init_flags = _filter_init_flags):
    f = ifilter.LoadIFilter(filename)
    f.Init(init_flags)
    while True:
        try:
            chunk_id, break_type, flags, locale, (propset_guid, prop_id), chunk_source_id, start, len =  f.GetChunk()
            prop_name = prop_id_to_name(prop_id)
            if flags == CHUNK_TEXT
                yield prop_name, text_for_current_chunk(f)
            
        except pythoncom.com_error, e:
            if e[0] == FILTER_E_END_OF_CHUNKS:
                break
            else:
                raise

        
