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

# do the search and get the results
my $res = $db->searchStructured('', '', '', '', [['author', $ARGV[0] ]]);

if ($res->end_rank)
{
    # print a summary of the results
    print $res->start_rank + 1 ." to ". $res->end_rank ." of ".
        $res->matches_human_readable_estimate . " results:\n";
    
    foreach (@{$res->results})
    {
        print "(". ($_->rank + 1) .") ". $_->data->{'title'}->[0] ."\n";
    }
}
else
{
    print "no results\n";
}