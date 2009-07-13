import re
WINDOW = 50   # trial and error...

# chunks are tags, words and punctuation, with trailing spaces
chunk_re = re.compile(r'<\w+[^>]*>\s*|</\w+>\s*|[\w\'\-]+\s*|[^\w\'\-\s]+\s*')
#word_re = re.compile(r'[\w\'\-]+|\d+\.\d+')
query_re = re.compile(r'"[^"]+"|[\w\'\-]+')

class Highlighter:

    def __init__(self, language_code='en'):
        """Create a new highlighter for the specified language.
        
        """
#        self.stem = .Stem(language_code)
        self.stem = lambda x: x

    def makeSample(self, text, query, maxlen=100, hl='{}'):
        """Make a context-sensitive sample with optional highlights
        
        `text` is the source text to summarise.
        `query` is an iterable of normalised query terms
        `maxlen` is the maximum length of the generated summary.
        `maxwords` is the maximum number of words in the generated summary.
        `hl` is a pair of strings to insert around highlighted terms, e.g. ('<b>', '</b>')
        """
        if isinstance (text, unicode):
            text = text.encode('utf-8')
        
        words = [w for w in chunk_re.findall(text) if w[0] != '<']
        lenwords = len(words)
        terms = [self._normalise_text(w) for w in words]
        
        if lenwords == 0: return text
    
        scores = [0] * lenwords
        highlight = [False] * lenwords    
    
        # find query words/phrases, and mark
        for n in xrange(lenwords):
            for q in query:
                try:
                    for offset, term in enumerate(q):
                        if terms[n+offset] != term:
                            raise IndexError    # could also be raised by falling off end
                
                    # match found - add scores
                    for offset, term in enumerate(q):
                        scores[n+offset] += WINDOW 
                        highlight[n+offset] = True
                    
                    # scores taper in either direction
                    for w in xrange(1, WINDOW):
                        l = n - w
                        if l < 0: break
    #                    if not word_re.match(words[l]): break
                        scores[l] += WINDOW - w
                        
                    for w in xrange(1, WINDOW):
                        r = n + offset + w
                        if r == lenwords: break
                        scores[r] += WINDOW - w
                    
                    break  # go on to next word
                
                except IndexError:
                    pass
        
        # flatten scoring loop
        scoreboard = {}
        for n in xrange(lenwords):
            scoreboard.setdefault(scores[n], []).append(n)
    
        # select words, highest scores first
        selected = [False] * lenwords
        charlen = 0
        try:
            for s in xrange(max(scores), -1, -1):
                if scoreboard.has_key(s):
                    for n in scoreboard[s]:
                        charlen += len(words[n]) + 1
                        if charlen >= maxlen:
                            raise StopIteration
                        selected[n] = True
        
        except StopIteration:
            pass
    
        # create sample
        sample = []
        in_phrase = False
        for n in xrange(lenwords):
            if selected[n]:
#                if in_phrase and word_re.match(words[n]):
#                    sample.append(' ')
                in_phrase = True
                if highlight[n]:
                    sample.append(hl[0])
                    sample.append(words[n])
                    sample.append(hl[1])
                else:
                    sample.append(words[n])
                
            elif in_phrase:
                sample.append('... ')
                in_phrase = False
    
        return ''.join(sample)

    def highlight(self, text, query, hl='{}', no_tags=True):
        """
        Add highlights (string prefix/postfix) to a string.
        
        `text` is the source to highlight.
        `query` is an iterable of normalised query terms
        `hl` is a pair of highlight strings, e.g. ('<i>', '</i>')
        `no_tags` strips HTML markout iff True
        """
        if isinstance (text, unicode):
            text = text.encode('utf-8')

        words = chunk_re.findall(text)
        if no_tags:
            words = [w for w in words if w[0] != '<']
        lenwords = len(words)
        terms = [self._normalise_text(w) for w in words]

        highlight = [False] * lenwords    
    
        # find query words/phrases, and mark
        for n in xrange(lenwords):
            for q in query:
                try:
                    for offset, term in enumerate(q):
                        if terms[n+offset] != term:
                            raise IndexError
                            
                    for offset, term in enumerate(q):
                        highlight[n+offset] = True

                except IndexError:
                    pass

        sample = []
        for n in xrange(lenwords):
#            if n and word_re.match(words[n]):
#                sample.append(' ')
            if highlight[n]:
                sample.append(hl[0])
                sample.append(words[n])
                sample.append(hl[1])
            else:
                sample.append(words[n])

        return ''.join(sample)

    
    def _normalise_text(self, term):
        # remove trailing spaces from words, and stem
        return self.stem(term.rstrip().lower())    
    
    def make_hl_terms(self, kwargs):
        """Process a dictionary to produce terms for highlighting etc.
        
        This is very NLA-specific and thus a bit hacky, but it allows us to unroll
        the term processing from render loops.
        """
        def _normalise(term):
            if term[0] == '"' and term[-1] == '"':
                term = term[1:-1]
    
            return [self.stem(x) for x in term.lower().split()]

        ret = []
        ret.extend(query_re.findall(kwargs.get('q', '')))
        ret.extend(query_re.findall(kwargs.get('q_any', '')))
        ret.extend(query_re.findall(kwargs.get('q_all', '')))
        if kwargs.get('q_phrase'):
            ret.append(kwargs['q_phrase'])

        # for CSE
        ret.extend(query_re.findall(kwargs.get('query', '')))
        ret.extend(query_re.findall(kwargs.get('queryany', '')))
        ret.extend(query_re.findall(kwargs.get('queryall', '')))
        if kwargs.get('queryphrase'):
            ret.append(kwargs['queryphrase'])
        
        ret = [_normalise(r) for r in ret]
        return ret

if __name__ == '__main__':
    import sys
    import time 
     
    text = """
Mandrake Tim Walker mandrake@telegraph.co.uktelegraph.co.uk/mandrake
After The Daily Telegraph&#x27;s disclosure that he routinely claimed
the maximum parliamentary food allowance of &#xA3;4,800 a year - proof, perhaps,
that he really does have bulimia nervosa, even if he hasn&#x27;t been especially
effective in shedding the pounds after his binge eating.
"""
    
    t0 = time.time()
    hl = Highlighter()
    print hl.makeSample(text, hl.make_hl_terms({'q':'mandrake'}), 400)
    print
    print hl.highlight(text, hl.make_hl_terms({'q':'mandrake'}))
#    print 1000* (time.time() - t0), 'ms'

