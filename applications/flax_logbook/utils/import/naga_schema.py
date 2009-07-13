
_text = {'type':'text', 'store':False, 'freetext':{'language':'en'}}
_filt = {'type':'text', 'store':False, 'exacttext':True}
_date = {'type':'text', 'store':False} # FIXME
_disp = {'type':'text', 'store':False}

fields = (
    ('text', _text, 'Text', True),  # fieldname, type, label, display? 
    ('caption', _text), 
    ('title', _text), 
    ('person', _filt), 
    ('medium', _filt), 
    ('ethnicgroup', _filt), 
    ('location', _filt), 
    ('date', _date), 
    ('keywords', _filt), 
    ('note', _disp), 
    ('acquirer/date', _date), 
    ('acquirer/form', _filt), 
    ('acquirer/person', _filt), 
    ('acquirer/refnum', _filt), 
    ('acquirer/note', _disp), 
    ('clip/caption', _text), 
    ('collection/date', _date), 
    ('collection/ethnicgroup', _filt), 
    ('collection/form', _filt), 
    ('collection/location', _filt), 
    ('collection/note', _disp), 
    ('collection/person', _filt), 
    ('collection/refnum', _filt), 
    ('production/date', _date), 
    ('production/ethnicgroup', _filt), 
    ('production/location', _filt), 
    ('production/note', _filt), 
    ('production/person', _filt), 
    ('production/refnum', _filt), 
    ('production/form', _filt), 
    ('id', _filt), 
    ('_bamboo_doc', {'type':'text', 'store':True}) 
)
