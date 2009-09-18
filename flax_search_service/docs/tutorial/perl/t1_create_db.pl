#!/usr/bin/perl

use strict;
use warnings;
use Error qw(:try);

use Flax;
use Flax::Error;
use Flax::Field;
use Flax::SummarySettings;

my $flax = Flax->new('url'=>'http://localhost:8080');
my $db = $flax->createDatabase('books');

# add some field definitions
$db->addField('title', Flax::Field::FreeText->new('store'=>1, 'lang'=>'en'));
$db->addField('first', Flax::Field::FreeText->new('store'=>0, 'lang'=>'en'));
$db->addField('author', Flax::Field::ExactText->new('store'=>1));