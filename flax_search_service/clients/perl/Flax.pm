# Copyright (c) 2009 Cognidox Ltd
# http://www.cognidox.com/
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

package Flax;

use strict;
use warnings;

use Error qw(:try);
use Flax::Database;
use Flax::RestClient;
use Flax::Util qw(flax_uri_escape);

require Exporter;

our @ISA = qw(Exporter);
our %EXPORT_TAGS = (
    'all' => [ qw( ) ]
);

our @EXPORT_OK = ( @{ $EXPORT_TAGS{'all'} } );
our @EXPORT = qw( );

our $VERSION = '0.01';

sub new {
    my $class = shift;
    my %params = @_;
    my $self = \%params;
    bless($self, $class);
    $self->_init;
    return $self;
}

sub _init {
    my $self = shift;
    $self->{'url'} ||= "";
    $self->{'url'} =~ s/^\s+|\s+$//gs;
    $self->{'url'} =~ s:([^/])$:$1/:;
    $self->{'restclient'} = Flax::RestClient->new('url' => $self->{'url'}, 
                                                  'version' => 1);
}

sub restclient {
    my $self = shift;
    return $self->{'restclient'};
}

sub getDatabase {
    my $self = shift;
    my $name = shift;
    my $res = $self->restclient->do_get('dbs/' . flax_uri_escape($name));
    if ($res->is_success) {
        return Flax::Database->new('client' => $self->restclient,
                                   'name' => $name);
    } else {
        throw Flax::Error::Database($res->content);
    }
}

sub createDatabase {
    my $self = shift;
    my $name = shift;
    my $overwrite = shift || 0;
    my $reopen = shift || 0;
    my $res = $self->restclient->do_post('dbs/' . flax_uri_escape($name),
                                         { 'overwrite' => $overwrite ? 1 : 0,
                                           'reopen' => $reopen ? 1 : 0 });
    if (!$res->is_success) {
        throw Flax::Error::Database('database could not be created (' .
                                    $res->content . ')');
    }
    return Flax::Database->new('client' => $self->restclient, 'name' => $name);
}

1;
__END__

=head1 NAME

Flax - Perl extension for interfacing with Flax, a Xapian based search engine.

=head1 SYNOPSIS

    use Flax;

    my $flax = Flax->new( 'url' => 'http://flax.example.com:8080' );
    my $db = $flax->getDatabase( 'my_documents' );
    my $results = $db->searchSimple( 'some text' );

=head1 DESCRIPTION

This module provides a client for interfacing with a FlaxSearchServerIndex
system. The Flax object provides access to Flax databases, on which queries
are run.

=head1 Flax CLASS

This class represents a connection to an instance of FSS.

=head2 METHODS

=head3 new (B<url> => I<url>)

=over 4

Creates a new Flax object connected to the Flax search server specified by
I<url>.

=back

=head3 createDatabase (I<dbname>, I<overwrite>, I<reopen>)

=over 4

Creates a new Flax database with the name I<dbname> and returns the database
object if it is created successfully.

Throws a Flax::Error::Database error if it is not possible to create the
database.

=back

=head3 getDatabase (I<dbname>)

=over 4

Returns a database object with the name I<dbname>.

If no database is found with the requested name, a Flax::Error::Database 
error is thrown.

=back

=head1 Flax::Database CLASS

Database objects encapsulate most of the API's functionality.

=head2 METHODS

=head3 delete

=over 4

Deletes the database resource referenced by this object.

=back

=head3 commit

=over 4

This is a temporary method, until the write caching mechanism in the FSS is
finalised. It causes all document additions and deletions to be committed to
the database, making them available to searches.

=back

=head3 getDocCount

=over 4

Returns a count of the documents in the database.

=back

=head3 addDocument (I<docdata>, I<docid>)

=over 4

Adds the document supplied as a HASH reference (I<docdata>) to the database. 
If I<docid> is supplied, this will be the document's ID (overwriting any 
existing document with this ID). Otherwise a new ID will be generated.

=back

=head3 getDocument (I<docid>)

=over 4

Returns the document identified by I<docid>. The document is returned as a 
a HASH reference.

See the FSS API documentation for a description of the data structure.

=back

=head3 deleteDocument (I<docid>)

=over 4

Deletes the document identified by I<docid> from the database.

Throws a Flax::Error::Document error if the document does not exist.

=back

=head3 addField (I<fieldname>, I<settings>)

=over 4

Adds a field definition with the specified I<fieldname> and I<settings>, 
where the latter is an instance of Flax::Field (see below). 

Throws a Flax::Error::Field error if the field already exists.

=back

=head3 getField (I<fieldname>)

=over 4

Returns a Flax::Field object representing the settings for the named field 
(see FSS API documentation for a description of this data structure). 

Throws a Flax::Error::Field error if the named field does not exist.

=back

=head3 replaceField (I<fieldname>, I<settings>)

=over 4

Adds a field definition with the specified I<fieldname> and settings, 
where the latter is an instance of Flax::Field (see below).

Throws a Flax::Error::Field error if the field already exists.

=back

=head3 deleteField (I<fieldname>)

=over 4

Delete the named I<fieldname> from this database's schema.

Throws a Flax::Error::Field error if the field does not exist.

=back

=head3 getFieldNames

=over 4

Returns a list of names of fields in this database's schema.

=back

=head3 searchSimple (I<query>, I<startrank>, I<endrank>, I<summary>)

=over 4

Search for the words in I<query> in the database, and returns matching 
documents as a Flax::SearchResultSet object (see below). 
I<startrank> and I<endrank> specify the start and end indexes (zero-based) 
of the set of documents to return.

I<summary> is an optional Flax::SummarySettings object, to cause the 
server to generate summaries (see below).

=back

=head3 searchStructured (I<queryAll>, I<queryAny>, I<queryNone>, I<queryPhrase>, I<filters>, I<startrank>, I<endrank>, I<summary>)

=over 4

A more complex search API which can be used (for example) to implement 
"advanced search" GUIs:

The query parameters control how to match documents:

=over 4

=item I<queryAll> - All words in this subquery must be matched.

=item I<queryAny> - At least one word must be matched.

=item I<queryNone> - Exclude documents containing any of these words.

=item I<queryPhrase> - Matches an exact phrase.

=back

I<filters> is an ARRAY reference containing two element ARRAY references
consisting of a fieldname and value. e.g.

C<my $filter = [ ['category', 'sport'], ['source', 'Reuters']];>

If multiple filters are supplied for the same field, they are combined with OR.
Between fields, filters are combined with AND.

=back

=head3 searchSimilar (I<id>, I<startrank>, I<endrank>, I<pcutoff>, I<summary>)

=head1 Flax::Field CLASS

Three Flax::Field classes can be used:

=over 4

=item Flax::Field::Text

=item Flax::Field::FreeText

=item Flax::Field::ExactText

=back

=head2 METHODS

=head3 new (store => I<store>, lang => I<lang>)

=head3 toJSON

=head1 Flax::SummarySettings CLASS

=head2 METHODS

=head3 new (I<fields>)

=over 4

Makes a new Flax::SummarySettings, using the list of I<fields> to summarize.

=back

=head3 summary_fields

=over 4

Get or set the summary fields.

=back

=head3 summary_maxlen

=over 4

Get or set the maximum number of characters to return in the summary.

=back

=head3 highlight_bra

=over 4

Get or set the string used to start a summary highlight.

=back

=head3 highlight_ket

=over 4

Get or set the string used to end a summary highlight.

=back

=head1 Flax::SearchResultSet CLASS

=head2 METHODS

=head3 results

=over 4

Returns an ARRAY reference of Flax::SearchResult objects.

=back

=head3 matches_estimated

=over 4

Get the estimated number of matched items.

=back

=head3 estimate_is_exact

=head3 matches_upper_bound

=head3 matches_human_readable_estimate

=head3 start_rank

=head3 end_rank

=head3 more_matches

=head1 Flax::SearchResult CLASS

=head2 METHODS

=head3 docid

=head3 rank

=head3 weight

=head3 db

=head3 data

=head1 REQUIREMENTS

Requires the following perl modules:

=over 4

=item Error
 
=item JSON (>= 2.0)

=item LWP

=item URI

=back

=head1 SEE ALSO

http://www.flax.co.uk - Flax web site

=head1 AUTHOR

Vittal Aithal, vittal.aithal@cognidox.com

http://www.cognidox.com/

=head1 COPYRIGHT AND LICENSE

Copyright (C) 2009 by Cognidox Ltd

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

=cut
