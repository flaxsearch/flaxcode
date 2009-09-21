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

# print the info
print $db->getDocCount ." documents in 'books'\n";
