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

package Flax::SummarySettings;

use strict;
use warnings;
use Flax::Util qw(flax_uri_escape);

use overload ('""' => 'stringify');

sub new {
    my $class = shift;
    my @fields = @_;
    my $self = {};
    bless( $self, $class );
    $self->_init(@fields);
    return $self;
}

sub _init {
    my $self = shift;
    $self->{'summary_fields'} = [ @_ ];
    $self->{'summary_maxlen'} = 500;
    $self->{'highlight_bra'} = '<b>';
    $self->{'highlight_ket'} = '</b>';
}

sub summary_fields {
    my $self = shift;
    if (@_) {
        $self->{'summary_fields'} = [ @_ ];
    }
    return @{$self->{'summary_fields'}};
}

sub summary_maxlen {
    my $self = shift;
    if (@_) {
        my $len = shift;
        if ($len =~ /^\d+$/) {
            $self->{'summary_maxlen'} = $len;
        }
    }
    return $self->{'summary_maxlen'};
}

sub highlight_bra {
    my $self = shift;
    if (@_) {
        $self->{'highlight_bra'} = shift;
    }
    return $self->{'highlight_bra'};
}

sub highlight_ket {
    my $self = shift;
    if (@_) {
        $self->{'highlight_ket'} = shift;
    }
    return $self->{'highlight_ket'};
}

sub stringify {
    my $self = shift;
    my $url = "&";
    $url .= join("&", map { "summary_field=" . 
                        flax_uri_escape($_) }
                           @{$self->{'summary_fields'}});
    return $url . "&summary_maxlen=" . $self->{'summary_maxlen'} .
           "&highlight_bra=" .
           flax_uri_escape($self->{'highlight_bra'}) .
           "&highlight_ket=" .
           flax_uri_escape($self->{'highlight_ket'});
}


1;
