# Introduction #

Early versions of Flax represented the type of a document by the file extension attached to a file.  This is fine for an initial prototype, but there are various problems associated with such a scheme; as a result, we should move to using a mime-type to describe the type of a file.  This isn't a perfect solution, but has various significant advantages.

## Type representation ##

We need an internal representation of the type of a file, so we can separate the detection of a file type from the filter we use to process it.  This needs to be displayable to users in a human-readable manner; both so that we can allow administrators to configure the mime-types which are indexed, and how they should be indexed, but also so that users can restrict their search to a given type of file.

The representation ideally needs to have the following properties:

  1. 1:1 mapping from actual type of file to type representation.
  1. 1:1 mapping from type representation to filters used to process that file.
  1. Extensible, to cope with new file formats being invented.
  1. Human readable (or easy to convert to a human readable representation).

It would also be nice to use a standardised scheme, so we don't have to re-invent the wheel, and so that we can take advantage of document sources which provide type information.

There are three obvious candidates for representation of file types:

  1. File extensions.
  1. Internal, ad-hoc scheme.
  1. Mime-type.

Obviously, an internal, ad-hoc scheme won't be standardised, so if we can address our requirements with a different scheme, we should do so.  I believe that mime-types satisfy the requirements, so I won't consider an ad-hoc scheme further.

## File extensions ##

The file extension (ie, those parts of the filename which follow a ".", such as ".doc" or ".pdf" or ".tgz", or ".tar.gz") often gives an indication of the file type.  However, it is unsatisfactory as a description of the type for the following reasons:

  * There may be multiple file types using a single extension.  For example, MS Word files are often stored with a ".doc" extension, but plain text files are often stored with the same extension.  Multimedia files are also often named with a common extension for very different content types; for example, ".ogg" is used to represent the "Ogg" container format, but the contents may be pure audio, pure video, or a mixture of the two.
  * There is no official registry of file extensions (which is partly a cause of the earlier problem), so there is no guarantee that the same file extension will be used by different programs for the same file type.
  * The file extension is easily changed (or removed) by users (particularly on Unix systems, which don't even give a warning to users before they do this), so there is a risk of information from the extension being unavailable.

## Mime types ##

Mime types were originally described to represent types of files attached to email messages, but they are now also widely used for documents obtained over HTTP.

Mime types are standardised, and there is an official registry for them, so in theory a given document should map to a single mime-type.  (Unfortunately, this mapping isn't perfect, as we will see later, but the situation is better than for file extensions.)

The standardisation should also mean that if we know the mime-type of a file, we can be sure of the contents of the file.  Critically, in practice, I believe this mapping is certainly good enough to allow us to implement mappings from file type to filter accurately enough.

There is also a standard mechanism for extending the mime-type mapping (using "x-" prefixed types), which means that we can accurately detect the type of a file.

Mime types also have the advantage of being split into a major and a minor type part - this may allow us to implement fallback filters based on just the major part for those mime-types for which we don't have a filter for the full mime-type.  (eg, we could have a default filter for "text/" which would be used to deal with a "text/html" document if there wasn't a filter specifically for "text/html")

Mime types are relatively human-readable, but since they are standardised, a mapping from the standard types to a human-readable description can reasonably easily be obtained.  Additional mappings could also be added for the extension types if necessary.


## Determining type information ##

Currently, Flax only retrieves documents directly from the filing system.  In most cases this means that there is no direct information available on the type of content in the file; so we need to determine the type ourselves in some way.

When we extend Flax to support documents which have been retrieved from web crawling, we should have type information available directly in mime-type form.  There may need to be some normalisation performed: for example, there are several different mime-types which effectively mean XHTML.  Also, such type information isn't 100% reliable: for example, some webservers are misconfigured, and others are deliberately configured (to work around browser bugs) to return text/html for XHTML documents, instead of text/xhtml.  However, in practice the space of mime-types is fairly well structured, and information returned from webservers can be used with only a few precautions.

We need to be able to determine the mime-type of a file on the filesystem.  Fortunately, the standard python "mimetypes" module will perform this lookup for us (and even allows new mime-types to be registered, or existing mappings to be altered), based on file extensions.  If we need greater accuracy, various databases of "magic" strings exist, which allow the mime-type to be determined from a combination of the file extension and the file contents, with minimal work.