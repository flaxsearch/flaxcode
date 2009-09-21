#!/usr/bin/perl

use strict;
use warnings;
use Error qw(:try);

use Flax;
use Flax::Error;
use Flax::Field;
use Flax::SummarySettings;

my $flax = Flax->new('url'=>'http://localhost:8080');
my $db = $flax->getDatabase('books');

# fetch and print the document
my $doc = $db->getDocument($ARGV[0]);
my $k;
my $v;
while (($k, $v) = each (%{$doc}))
{
    print "$k: ". join(', ', @$v) ."\n";
}
