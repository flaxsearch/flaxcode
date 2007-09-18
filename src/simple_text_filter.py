from __future__ import with_statement
import os
import itertools

def text_filter(filename):

    def start_fields():
        yield ("filename", filename)
        raise StopIteration

    def get_paragraphs():
        with open(filename) as f:
            for k, para in itertools.groupby(f, lambda x: "\n" == x):
                if not k: #get rid of the blank line groups
                    yield "text", ''.join(para)
                

    return itertools.chain(start_fields(), get_paragraphs())
