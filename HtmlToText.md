# The htmltotext module #

This python module extracts the
textual content and metadata from HTML pages.  It tries to cope with
invalid markup and incorrectly specified character sets, and strips out
HTML tags (splitting words at tags appropriately).  It also discards the
contents of script tags and style tags.

As well as text from the body of the page, it extracts the page title,
and the content of meta description and keyword tags.  It also parses
meta robots tags to determine whether the page should be indexed.

The HTML parser used by this module was extracted from the Xapian search
engine library (and specifically, from the omindex indexing utility in
that library).

## Latest sources ##

The latest sources for htmltotext live in the flaxcode SVN repository, under trunk/libs/htmltotext/