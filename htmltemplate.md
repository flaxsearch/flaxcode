I have a samll problem with HTMLTemplate. Perhaps I have missed
something, so I will describe the issue here.

There are some pieces of information can be determined at application
startup time that should affect the structure of web pages that we
serve, but do not need to be recomputed each time we render a
page. For example we have a set of formats that can be indexed. This
should not be hard coded.

Some templates (defining a document collection, doing a search)
present checkboxes allowing selection of a subset of the available
formats. The obvious way to deal with this in the template is to use
an HTMLTemplate repeater node: `node=rep:formats` that makes the
checkboxes. But then we are obliged to generate the checkboxes each
time we render the template. But all we actually need to do is set an
attribute to say which ones are checked.  We really want to
programmatically make the formats once as part of application
inialisation. The problem is that that HTMLTemplate DOM is really too
specialized.

Note that it's a slightly different situation with container nodes,
because you can just assign other nodes to them at startup. But for
repeaters each time you use the `.repeat()` method of the repeater a
new html fragment is made, so we can't use it once to make the format
checkboxes at initialization and again to set which ones are checked
at page render time.
