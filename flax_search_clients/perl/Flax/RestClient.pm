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

package Flax::RestClient;

use strict;
use warnings;

use HTTP::Request;
use JSON 2.0;
use LWP::UserAgent;
use URI;
use Flax::RestResult;


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
    $self->{'url'} ||= '';
    $self->{'version'} ||= 1;
    $self->{'url'} .= "v" . $self->{'version'} . "/";
}

sub baseurl {
    my $self = shift;
    return $self->{'url'};
}

sub version {
    my $self = shift;
    return $self->{'version'};
}

sub do_get {
    my $self = shift;
    my $path = shift || "";
    my $params = shift;
    
    my $uri = new URI($self->baseurl . $path);
    if (defined($params)) {
        $uri->query_form($params);
    }
    return $self->_do_http_request($uri->as_string, 'GET');
}

sub do_post {
    my $self = shift;
    my $path = shift;
    my $data = shift || '';
    return $self->_do_http_request($self->baseurl . $path, 'POST', $data);
}

sub do_put {
    my $self = shift;
    my $path = shift;
    my $data = shift || '';
    return $self->_do_http_request($self->baseurl . $path, 'PUT', $data);
}

sub do_delete {
    my $self = shift;
    my $path = shift;
    return $self->_do_http_request($self->baseurl . $path, 'DELETE');
}

sub _do_http_request {
    my $self = shift;
    my $url = shift;
    my $method = shift || 'GET';
    my $content = shift;

    my $json = new JSON;
    my $req = HTTP::Request->new($method, $url);
    if ($content) {
        $req->content($json->encode($content));
        $req->header('Content-type' => 'text/json');
    }

    my $ua = LWP::UserAgent->new();
    $ua->timeout(30);
    $ua->agent('Flax-Perl client/' . $Flax::VERSION);
    my $res = $ua->request($req);
    my $loc = $res->header('Location') || '';
    if ($res->is_success()) {
        return Flax::RestResult->new('code' => $res->code,
                                     'content' => $json->decode($res->content),
                                     'location' => $loc);
    } else {
        return Flax::RestResult->new('code' => $res->code,
                                     'content' => $res->content,
                                     'location' => $loc);
    }
}


1;
