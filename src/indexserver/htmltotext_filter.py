from __future__ import with_statement
import htmltotext

def html_filter(filename):
    with open(filename) as f:
        html = f.read()
        p = htmltotext.extract(html)
        yield "title", p.title
        yield "content", p.content
        yield "description", p.description
        kw = p.keywords.strip()
        if len(kw) != 0:
            for keyword in kw.split(','):
                yield "keyword", p.keywords
        yield "invalid", "he he"
