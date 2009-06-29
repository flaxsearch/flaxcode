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

package Flax::Field;

use strict;
use warnings;
use Error qw(:try);
use Flax::Error;

sub new {
    my $class = shift;
    my (%params) = @_;
    my $self = \%params;
    $self->{'store'} ||= 0;
    bless( $self, $class );
    return $self;
}

sub store {
    my $self = shift;   
    return $self->{'store'};
}

sub fromJSON {
    my $json = shift;
    my $store = $json->{'store'};

    if ($json->{'type'} eq 'text') {
        if (exists $json->{'freetext'}) {
            return Flax::Field::FreeText->new('store' => $store,
                                              'lang' => $json->{'freetext'}->{'language'});
        } elsif (exists $json->{'exacttext'}) {
            return Flax::Field::ExactText->new('store' => $store);
        } else {
            throw Flax::Error::Field('unsupported text field parameters');
        }
    } else {
        throw Flax::Error::Field('unsupported field type');
    }
}

package Flax::Field::Text;
use base 'Flax::Field';

sub toJSON {
    my $self = shift;
    return { 'type' => 'text', 'store' => 1 };
}

package Flax::Field::FreeText;
use base 'Flax::Field::Text';

use overload ('""' => 'stringify');

sub lang {
    my $self = shift;   
    return $self->{'lang'};
}

sub toJSON {
    my $self = shift;
    my $json = { 'type' => 'text', 'store' => $self->{'store'} };
    if (exists $self->{'lang'} && $self->{'lang'}) {
        $json->{'freetext'} = { 'language' => $self->{'lang'} };
    } else {
        $json->{'freetext'} = { };
    }
    return $json;
}

sub stringify {
    my $self = shift;
    return "FlaxFreeTextField[" . $self->store . ", " . 
        ($self->lang ? $self->lang : "") . "]";
}

package Flax::Field::ExactText;
use base 'Flax::Field::Text';

use overload ('""' => 'stringify');

sub toJSON {
    my $self = shift;
    return { 'type' => 'text',
             'store' => $self->store,
             'exacttext' => 1 };
}

sub stringify {
    my $self = shift;
    return "FlaxExactTextField[" . $self->store . "]";
}


1;
