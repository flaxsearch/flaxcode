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

package Flax::SearchResultSet;

use strict;
use warnings;
use Flax::SearchResult;

sub new {
    my $class = shift;
    my $json = shift;
    my $self = {};
    $self->{'results'} = [];
    if (exists $json->{'results'} && scalar(@{$json->{'results'}})) {
        foreach my $r (@{$json->{'results'}}) {
            push(@{$self->{'results'}},
                 Flax::SearchResult->new($r));
        }
    }
    foreach (qw(matches_estimated matches_lower_bound 
                matches_upper_bound matches_human_readable_estimate
                start_rank end_rank)) {
        if (exists $json->{$_}) {
            $self->{$_} = $json->{$_};
        }
    }
    foreach (qw(more_matches estimate_is_exact)) {
        $self->{$_} =
            (exists $json->{$_} && $json->{$_} == JSON::true) ? 1 : 0;
    }
    bless( $self, $class );
    return $self;
}

sub results {
    my $self = shift;
    return $self->{'results'};
}

sub matches_estimated {
    my $self = shift;
    return $self->{'matches_estimated'};
}

sub estimate_is_exact {
    my $self = shift;
    return $self->{'estimate_is_exact'};
}

sub matches_lower_bound {
    my $self = shift;
    return $self->{'matches_lower_bound'};
}

sub matches_upper_bound {
    my $self = shift;
    return $self->{'matches_upper_bound'};
}

sub matches_human_readable_estimate {
    my $self = shift;
    return $self->{'matches_human_readable_estimate'};
}

sub start_rank {
    my $self = shift;
    return $self->{'start_rank'};
}

sub end_rank {
    my $self = shift;
    return $self->{'end_rank'};
}

sub more_matches {
    my $self = shift;
    return $self->{'more_matches'};
}


1;
