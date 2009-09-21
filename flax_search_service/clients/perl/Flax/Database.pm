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

package Flax::Database;

use strict;
use warnings;

use Error qw(:try);
use URI;
use JSON;
use Flax::Error;
use Flax::Field;
use Flax::SearchResultSet;
use Flax::Util qw(flax_uri_escape);

sub new {
    my $class = shift;
    my (%params) = @_;
    my $self = \%params;
    bless( $self, $class );
    $self->_init();
    return $self;
}

sub _init {
    my $self = shift;
    $self->{'client'} ||= undef;
    $self->{'name'} ||= '';
    $self->{'deleted'} = 0;
}

sub dbname {
    my $self = shift;
    return $self->{'name'};
}

sub restclient {
    my $self = shift;
    return $self->{'client'};
}

sub deleted {
    my $self = shift;
    return ($self->{'deleted'} ? 1 : 0);
}

sub _toString {
    my $self = shift;
    return "Flax::Database[" . $self->dbname . ($self->deleted ? 'deleted' : '');
}

sub _baseUrl {
    my $self = shift;
    return 'dbs/' . flax_uri_escape($self->dbname);
}

sub _checkDeleted {
    my $self = shift;
    if ($self->deleted) {
        throw Flax::Error::Database('database has been deleted');
    }
}

sub delete {
    my $self = shift;
    my $res = $self->restclient->do_delete($self->_baseUrl);
    throw Flax::Error::Database($res->content) unless ($res->is_success);
    $self->{'deleted'} = 1;
}

sub getDocCount {
    my $self = shift;
    $self->_checkDeleted();
    my $res = $self->restclient->do_get($self->_baseUrl);
    throw Flax::Error::Field($res->content) unless ($res->is_success);
    return $res->content->{'doccount'};
}

sub getFieldNames {
    my $self = shift;
    $self->_checkDeleted();
    my $res = $self->restclient->do_get($self->_baseUrl . '/schema/fields');
    throw Flax::Error::Field($res->content) unless ($res->is_success);
    return $res->content;
}

sub getField {
    my $self = shift;
    my $fieldname = shift;
    $self->_checkDeleted();
    my $res = $self->restclient->do_get($self->_baseUrl . '/schema/fields/' .
                                        flax_uri_escape($fieldname));
    throw Flax::Error::Field($res->content) unless ($res->is_success);
    return Flax::Field::fromJSON($res->content);
}

sub addField {
    my $self = shift;
    my $fieldname = shift;
    my $fielddesc = shift;
    $self->_checkDeleted();
    my $res = $self->restclient->do_post($self->_baseUrl . '/schema/fields/' .
                                         flax_uri_escape($fieldname),
                                         $fielddesc->toJSON());
    throw Flax::Error::Field($res->content) unless ($res->is_success);
}

sub replaceField {
    my $self = shift;
    my $fieldname = shift;
    my $fielddesc = shift;
    $self->_checkDeleted();
    my $res = $self->restclient->do_put($self->_baseUrl . '/schema/fields/' .
                                        flax_uri_escape($fieldname),
                                        $fielddesc->toJSON());
    throw Flax::Error::Field($res->content) unless ($res->is_success);
}

sub deleteField {
    my $self = shift;
    my $fieldname = shift;
    $self->_checkDeleted();
    my $res = $self->restclient->do_delete($self->_baseUrl . '/schema/fields/' .
                                           flax_uri_escape($fieldname));
    throw Flax::Error::Field($res->content) unless ($res->is_success);
}

sub getDocument {
    my $self = shift;
    my $docid = shift;
    $self->_checkDeleted();
    my $res = $self->restclient->do_get($self->_baseUrl . '/docs/' .
                                        flax_uri_escape($docid));
    throw Flax::Error::Document($res->content) unless ($res->is_success);
    return $res->content;
}

sub addDocument {
    my $self = shift;
    my $docdata = shift;
    my $docid = shift || "";
    $self->_checkDeleted();
    my $res;
    if ($docid) {
        $res = $self->restclient->do_post($self->_baseUrl . '/docs/' .
                                          flax_uri_escape($docid), $docdata);
    } else {
        $res = $self->restclient->do_post($self->_baseUrl . '/docs', $docdata);
    }
    throw Flax::Error::Document($res->content) unless ($res->is_success);
    return $res->content;
}

sub deleteDocument {
    my $self = shift;
    my $docid = shift;
    $self->_checkDeleted();
    my $res = $self->restclient->do_delete($self->_baseUrl . '/docs/' .
                                           flax_uri_escape($docid));
    throw Flax::Error::Document($res->content) unless ($res->is_success);
}

sub flush {
    my $self = shift;
    $self->_checkDeleted();
    my $res = $self->restclient->do_post($self->_baseUrl . '/flush', JSON::true);
    throw Flax::Error::Database($res->content) unless ($res->is_success);
}

sub searchSimple {
    my $self = shift;
    my $query = shift;
    my $startrank = shift;
    my $endrank = shift;
    my $summary = shift;
    $self->_checkDeleted();
    if (!$startrank || $startrank !~ /^\d+$/) {
        $startrank = 0;
    }
    if (!$endrank || $endrank !~ /^\d+$/) {
        $endrank = 10;
    }
    my $uri = URI->new($self->_baseUrl . "/search/simple");
    my $settings = '';
    $uri->query_form( 'query' => $query,
                      'start_rank' => $startrank,
                      'end_rank' => $endrank
                    );
    my $url = $uri->as_string;
    if ($summary && ref($summary) eq 'Flax::SummarySettings') {
        $url .= "$summary";
    }

    my $res = $self->restclient->do_get($url);
    throw Flax::Error::Document->new($res->content) unless ($res->is_success);
    return Flax::SearchResultSet->new($res->content);
}

sub searchStructured {
    my $self = shift;
    my $queryAll = shift;
    my $queryAny = shift;
    my $queryNone = shift;
    my $queryPhrase = shift;
    my $filters = shift;
    my $startrank = shift;
    my $endrank = shift;
    my $summary = shift;

    $self->_checkDeleted();

    if (!$startrank || $startrank !~ /^\d+$/) {
        $startrank = 0;
    }
    if (!$endrank || $endrank !~ /^\d+$/) {
        $endrank = 10;
    }
    my $uri = URI->new($self->_baseUrl . "/search/structured");
    $uri->query_form(
            'start_rank' => $startrank,
            'end_rank' => $endrank,
            'query_all' => flax_uri_escape($queryAll),
            'query_any' => flax_uri_escape($queryAny),
            'query_none' => flax_uri_escape($queryNone),
            'query_phrase' => flax_uri_escape($queryPhrase));
    my $url = $uri->as_string;
    if ($summary && ref($summary) eq 'Flax::SummarySettings') {
        $url .= "$summary";
    }
    if ($filters && ref($filters) eq 'ARRAY') {
        foreach my $f (@$filters) {
            if (ref($f) eq 'ARRAY') {
                $url .= "&filter=" . 
                        join(":", map { flax_uri_escape($_) }
                            @$f);
            }
        }
    }
    my $res = $self->restclient->do_get($url);
    throw Flax::Error::Document->new($res->content) unless ($res->is_success);
    return Flax::SearchResultSet->new($res->content);
}

sub searchSimilar {
    my $self = shift;
    my $id = shift;
    my $startrank = shift;
    my $endrank = shift;
    my $pcutoff = shift;
    my $summary = shift;

    $self->_checkDeleted();

    if (!$startrank || $startrank !~ /^\d+$/) {
        $startrank = 0;
    }
    if (!$endrank || $endrank !~ /^\d+$/) {
        $endrank = 10;
    }
    my $uri = URI->new($self->_baseUrl . "/search/similar");
    $uri->query_form(
            'start_rank' => $startrank,
            'end_rank' => $endrank,
            'id' => flax_uri_escape($id));
    my $url = $uri->as_string;
    if ($summary && ref($summary) eq 'Flax::SummarySettings') {
        $url .= "$summary";
    }
    if ($pcutoff && $pcutoff =~ /^\d+$/) {
        $url .= "&pcutoff=$pcutoff";
    }
    my $res = $self->restclient->do_get($url);
    throw Flax::Error::Document->new($res->content) unless ($res->is_success);
    return Flax::SearchResultSet->new($res->content);
}
    
1;
