#$Id : xxx $
import itertools
import pythoncom
import pywintypes
import itertools
from win32com.ifilter import ifilter
from win32com.ifilter.ifiltercon import *
from win32com.storagecon import *
import util
import logging

log = logging.getLogger("filter.ifilter")

prop_id_map = { 19 : "content",
                 3 : "HtmlHeading1" }


def prop_id_to_name(prop_id):
    if type(prop_id) is str:
        return prop_id
    elif prop_id in prop_id_map:
        return prop_id_map[prop_id]
    else:
        return prop_id


def text_for_current_chunk(filt):
    def get_text():
        while True:
            yield filt.GetText()

    return(util.gen_until_exception(get_text(),
                                    pythoncom.com_error, 
                                    lambda e: e[0] == FILTER_E_NO_MORE_TEXT))

_filter_init_flags = IFILTER_INIT_INDEXING_ONLY | \
                     IFILTER_INIT_CANON_PARAGRAPHS | \
                     IFILTER_INIT_APPLY_INDEX_ATTRIBUTES | \
                     IFILTER_INIT_APPLY_CRAWL_ATTRIBUTES| \
                     IFILTER_INIT_APPLY_OTHER_ATTRIBUTES | \
                     IFILTER_INIT_SEARCH_LINKS

def ifilter_filter(filename, init_flags = _filter_init_flags):
    pythoncom.CoInitialize()
    filt, stg = get_ifilter_for_file(filename)
    init_flags = filt.Init(init_flags)

    def start_fields():
        if init_flags == IFILTER_FLAGS_OLE_PROPERTIES and stg:
           try:
               pss = stg.QueryInterface(pythoncom.IID_IPropertySetStorage)
               ps = pss.Open(PSGUID_SUMMARYINFORMATION)
               props_to_read = (PIDSI_TITLE, PIDSI_SUBJECT, PIDSI_AUTHOR, PIDSI_KEYWORDS, PIDSI_COMMENTS)
               title, subject, author, keywords, comments = ps.ReadMultiple(props_to_read)
               if title:
                   yield 'title', title
               if subject:
                   yield 'subject', subject
               if author:
                   yield 'author', author
               if keywords:
                   for k in keywords.split():
                       yield 'keyword', k
               if comments:
                   yield 'comments', comments
           except pythoncom.com_error, e:
               pass
               

    def do_chunks():
        while True:
            chunk_id, break_type, flags, locale, (propset_guid, prop_id), chunk_source_id, start, len = filt.GetChunk()
            prop_name = prop_id_to_name(prop_id)
            if flags == CHUNK_TEXT:
                for txt in text_for_current_chunk(filt):
                    yield prop_name, txt
        
    return itertools.chain(start_fields(),
                           util.gen_until_exception(do_chunks(),
                                                    pythoncom.com_error,
                                                    lambda e: e[0] == FILTER_E_END_OF_CHUNKS))
        
def load_ifilter(filename):
    try:
        return ifilter.LoadIFilter(filename)
    except pythoncom.com_error, e:
        if e[0] == FILTER_E_UNKNOWNFORMAT:
            log.warning("File %s is not a recognized format" % filename)
        else:
            log.warning("File %s cannot be processed" % filename)
        raise
        
    

def get_ifilter_for_file(filename):
    """
    Deal with structured storage file if possible. 
    See http://msdn2.microsoft.com/en-us/library/aa380369.aspx
    """

    if pythoncom.StgIsStorageFile(filename):
        storage_init_flags = STGM_READ | STGM_SHARE_DENY_WRITE
        stg = pythoncom.StgOpenStorage(filename, None, storage_init_flags)
        try:
            filt = ifilter.BindIFilterFromStorage(stg)
        except pythoncom.com_error, e:
            if e[0] == -2147467262:
                filt = load_ifilter(filename)
            else:
                raise
    else:
        filt = load_ifilter(filename)
        stg = None
    return (filt, stg)
