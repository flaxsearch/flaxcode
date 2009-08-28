#!/usr/bin/perl

use strict;
use warnings;
use Data::Dumper;
use Error qw(:try);
use Test::Simple tests => 15;
use lib qw(../);

use Flax;
use Flax::Error;
use Flax::Field;
use Flax::SummarySettings;

my $url = shift(@ARGV);
if (!$url) {
    print "Please provide a Flax server URL\n";
    exit;
}

my $flax = Flax->new('url'=>$url);
ok( defined $flax );
ok( $flax->isa('Flax') );

my $dbname = "tmp" . time();

# Test database things
ok( testNoDatabase($flax, $dbname) );
ok( testCreateDeleteDatabase($flax, $dbname) );
ok( testDbNameCharacters($flax) );

# Test field things
my $db = $flax->createDatabase($dbname);
ok( testNoFields($db) );
ok( testAddDeleteFields($db) );
ok( testOverwriteField($db) );
$db->delete();

# Test document things
$db = $flax->createDatabase($dbname);
$db->addField('foo', Flax::Field::FreeText->new('store'=>1));
ok( testNoDoc($db) );
ok( testAddDoc($db) );
ok( testBigDoc($db) );
$db->delete();

# Test search things
$db = $flax->createDatabase($dbname);
ok( testExact($db) );
ok( testFreetext($db) );
ok( testFreetextStemmed($db) );
ok( testSimilar($db) );
$db->delete();


exit;

sub testNoDatabase {
    my $flax = shift;
    my $dbname = shift;
    try {
        $flax->getDatabase($dbname);
        return 0;
    }
    catch Flax::Error::Database with {
        return 1;
    }
}

sub testCreateDeleteDatabase {
    my $flax = shift;
    my $dbname = shift;
    my $db = $flax->createDatabase($dbname);
    return 0 unless (defined $db);
    $db = $flax->getDatabase($dbname);
    return 0 unless (defined $db);
    $db->delete();
    try {
        $flax->getDatabase($dbname);
        return 0;
    }
    catch Flax::Error::Database with {
        return 1;
    }
}

sub testDbNameCharacters {
    my $flax = shift;
    my $dbname = 'foo#$&!/bar*)({}';
    my $db = $flax->createDatabase($dbname);
    return 0 unless (defined $db);
    my $fields = $db->getFieldNames();
    return 0 unless (ref($fields) eq 'ARRAY');
    $db->delete();
    return 1;
}

sub testNoFields {
    my $db = shift;
    my $fnames = $db->getFieldNames();
    return 0 unless (ref($fnames) eq 'ARRAY');
    try {
        $db->getField('foo');
        return 0;
    }
    catch Flax::Error::Field with {
        return 1;
    }
}

sub testAddDeleteFields {
    my $db = shift;
    my $res = $db->addField('foo', Flax::Field::ExactText->new('store'=>1));
    $db->commit();
    my $fnames = $db->getFieldNames();
    return 0 unless ($fnames->[0] eq 'foo');
    my $field = $db->getField('foo');
    return 0 unless ("$field" eq 'FlaxExactTextField[1]');
    $db->deleteField('foo');
    $db->commit();
    try {
        $db->getField('foo');
        return 0;
    }
    catch Flax::Error::Field with {
        return 1;
    }
}

sub testOverwriteField {
    my $db = shift;
    my $res = $db->addField('foo', Flax::Field::ExactText->new('store' => 1));
    $db->commit();

    $res = $db->replaceField('foo', Flax::Field::FreeText->new('store' => 1));
    $db->commit();

    my $fnames = $db->getFieldNames();
    return 0 unless ($fnames->[0] eq 'foo');

    my $field = $db->getField('foo');
    return 0 unless ("$field" eq 'FlaxFreeTextField[1, ]');
    return 1;
}


sub testNoDoc {
    my $db = shift;
    try {
        my $doc = $db->getDocument('doc001');
        return 0;
    }
    catch Flax::Error::Document with {
        return 1;
    }
}

sub testAddDoc {
    my $db = shift;
    my $doc = { 'foo' => 'bar' };
    $db->addDocument($doc, 'doc002');
    $db->commit();

    return 0 unless ($db->getDocCount() == 1);

    my $doc2 = $db->getDocument('doc002');
    return 0 unless ($doc2->{'foo'}->[0] eq 'bar');
    
    my $res = $db->searchSimple('bar');
    return 0 unless ($res->matches_estimated == 1);

    $db->deleteDocument('doc002');
    $db->commit();

    try {
        $db->getDocument('doc002');
        return 0;
    }
    catch Flax::Error::Document with {
        return 1;
    }

    $res = $db->searchSimple('bar');
    return 0 unless ($res->matches_estimated == 0);
    return 1;
}

sub testBigDoc {
    my $db = shift;
    my $text=<<EOT;
Derrida began speaking and writing publicly at a time when the French
intellectual scene was experiencing an increasing rift between what could
broadly speaking be called "phenomenological" and "structural" approaches to
understanding individual and collective life. For those with a more
phenomenological bent, the goal was to understand experience by comprehending
and describing its genesis, the process of its emergence from an origin or
event. For the structuralists, this was precisely the false problem, and the
"depth" of experience could in fact only be an effect of structures which are
not themselves experiential. It is in this context that in 1959 Derrida asks the
question: must not structure have a genesis, and must not the origin, the point
of genesis, be already structured, in order to be the genesis of something?[9]
In other words, every structural or "synchronic" phenomenon has a history, and
the structure cannot be understood without understanding its genesis.[10] At the
same time, in order that there be movement, or potential, the origin cannot be
some pure unity or simplicity, but must already be articulated complex such that
from it a "diachronic" process can emerge. This originary complexity must not be
understood as an original positing, but more like a default of origin, which
Derrida refers to as iterability, inscription, or textuality.[11] It is this
thought of originary complexity, rather than original purity, which destabilises
the thought of both genesis and structure, that sets Derrida's work in motion,
and from which derive all of its terms, including deconstruction.[12] Derrida's
method consisted in demonstrating all the forms and varieties of this originary
complexity, and their multiple consequences in many fields. His way of achievingthis was by conducting thorough, careful, sensitive, and yet transformational
readings of philosophical and literary texts, with an ear to what in those texts
runs counter to their apparent systematicity (structural unity) or intended
sense (authorial genesis). By demonstrating the aporias and ellipses of thought,
Derrida hoped to show the infinitely subtle ways that this originary complexity,
which by definition cannot ever be completely known, works its structuring and
destructuring effects. At the very beginning of his philosophical career Derrida
was concerned to elaborate a critique of the limits of phenomenology. His first
lengthy academic manuscript, written as a dissertation for his diplome d'etudes
superieures and submitted in 1954, concerned the work of Edmund Husserl.[14] In
1962 he published Edmund Husserl's Origin of Geometry: An Introduction, which
contained his own translation of Husserl's essay. Many elements of Derrida's
thought were already present in this work. In the interviews collected in
Positions (1972), Derrida said: "In this essay the problematic of writing was
already in place as such, bound to the irreducible structure of 'deferral' in
its relationships to consciousness, presence, science, history and the history
of science, the disappearance or delay of the origin, etc. [...] this essay can
be read as the other side (recto or verso, as you wish) of Speech and
Phenomena."[15] Derrida first received major attention outside France with his
lecture, "Structure, Sign, and Play in the Discourse of the Human Sciences,"
delivered at Johns Hopkins University in 1966 (and subsequently included in
Writing and Difference). The conference at which this paper was delivered was
concerned with structuralism, then at the peak of its influence in France, but
only beginning to gain attention in the United States. Derrida differed from
other participants by his lack of explicit commitment to structuralism, having
already been critical of the movement. He praised the accomplishments of
structuralism but also maintained reservations about its internal limitations,
thus leading to the notion that his thought was a form of
post-structuralism.
(source: http://en.wikipedia.org/wiki/Derrida )
EOT
    $db->addDocument({ 'foo' => $text });
    $db->commit();

    my $res = $db->searchSimple('derrida');
    return 0 unless ($res->matches_estimated == 1);

    my $setting = Flax::SummarySettings->new('foo');
    my $res2 = $db->searchSimple('derrida', 0, 10, $setting);
    my $summary = $res2->results->[0]->data->{'foo'}->[0];
    my $highlight_bra = $setting->highlight_bra;
    my $highlight_ket = $setting->highlight_ket;
    return 0 unless ($summary =~ m#<b>Derrida</b>#);
    # Remove highlighting to check the returned length
    $summary =~ s/\Q$highlight_bra\E//gs;
    $summary =~ s/\Q$highlight_ket\E//gs;
    return 0 unless (length($summary) <= 500);
    return 1;
}

sub testExact {
    my $db = shift;
    $db->addField('f1', Flax::Field::ExactText->new());
    $db->addField('f2', Flax::Field::ExactText->new());

    $db->addDocument({'f1' => 'Billy Bragg', 'f2' => 'A New England'}, 'doc1');
    $db->addDocument({'f1' => 'Billy Bragg', 'f2' => 'Between The Wars'}, 'doc2');
    $db->commit();

    my $res1 = $db->searchStructured('', '', '', '',
                    [[ 'f2', 'A New England' ]]);
    return 0 unless ($res1->matches_estimated == 1);
    return 0 unless ($res1->results->[0]->docid eq 'doc1');

    my $res2 = $db->searchStructured('', '', '', '',
                    [[ 'f2', 'Between The Wars' ]]);
    return 0 unless ($res2->matches_estimated == 1);
    return 0 unless ($res2->results->[0]->docid eq 'doc2');

    my $res3 = $db->searchStructured('', '', '', '',
                    [[ 'f1', 'Billy Bragg' ]]);
    return 0 unless ($res3->matches_estimated == 2);

    my $res4 = $db->searchStructured('', '', '', '',
                    [[ 'f1', 'Billy Bragg' ], ['f2', 'A New England']]);
    return 0 unless ($res4->matches_estimated == 1);

    my $res5 = $db->searchStructured('', '', '', '',
                    [[ 'f1', 'Billy Bragg' ], ['f1', 'The Smiths'],
                     ['f2', 'A New England']]);
    return 0 unless ($res5->matches_estimated == 1);

    return 1;
}

sub testFreetext {
    my $db = shift;
    $db->addField('f1', Flax::Field::ExactText->new());
    $db->addField('f2', Flax::Field::FreeText->new());
    $db->addDocument({'f1' => 'Billy Bragg', 'f2' => 'A New England'}, 'doc1');
    $db->addDocument({'f1' => 'Billy Bragg', 'f2' => 'between the wars'}, 'doc2');
    $db->commit();

    # check search results (freetext search)
    my $res1 = $db->searchSimple('A New england');
    return 0 unless ($res1->matches_estimated == 1);
    return 0 unless ($res1->results->[0]->docid eq 'doc1');

    # check search results (freetext search)
    my $res2 = $db->searchStructured('Between The Wars', '', '', '');
    return 0 unless ($res2->matches_estimated == 1);
    return 0 unless ($res2->results->[0]->docid eq 'doc2');

    # search all
    my $res3 = $db->searchStructured('Between The Lines', '', '', '');
    return 0 unless ($res3->matches_estimated == 0);

    # search any
    my $res4 = $db->searchStructured('', 'England Between', '', '');
    return 0 unless ($res4->matches_estimated == 2);

    # search none
    my $res5 = $db->searchStructured('', 'England Between', 'wars', '');
    return 0 unless ($res5->matches_estimated == 1);

    # search any + filter
    my $res6 = $db->searchStructured('', 'England Between', '', '',
                    [['f1','Billy Bragg']]);
    return 0 unless ($res6->matches_estimated == 2);

    # search any + filter 2
    my $res7 = $db->searchStructured('', 'England Between', '', '',
                    [['f1', 'Melvin Bragg']]);
    return 0 unless($res7->matches_estimated == 0);
    
    return 1;
}

sub testFreetextStemmed {
    my $db = shift;

    $db->addField('f1', Flax::Field::FreeText->new('store'=>0, 'lang'=> 'en'));
    $db->addDocument({'f1' => 'A New England'}, 'doc1');
    $db->addDocument({'f1' => 'between the wars'}, 'doc2');
    $db->commit();

    my $res1 = $db->searchSimple('warring');
    return 0 unless ($res1->matches_estimated == 1);

    my $res2 = $db->searchSimple('warring between');
    return 0 unless ($res2->matches_estimated == 1);

    my $res3 = $db->searchSimple('war OR england');
    return 0 unless ($res3->matches_estimated == 2);

    return 1;
}

sub testSimilar {
    my $db = shift;
    $db->addField('f1', Flax::Field::FreeText->new('store'=>0, 'lang'=> 'en'));
    $db->addDocument({'f1' => 'Milkman Of Human Kindness'}, 'doc1');
    $db->addDocument({'f1' => 'Milk Of Human Kindness'}, 'doc2');
    $db->addDocument({'f1' => 'nothing'}, 'doc3');
    $db->commit();

    my $res1 = $db->searchSimilar('doc2');
    return 0 unless ($res1->matches_estimated == 2);
    return 0 unless ($res1->results->[0]->docid eq 'doc2');

    my $res2 = $db->searchSimilar('doc1', 0, 1, 100);
    return 0 unless ($res2->matches_estimated == 1);

    return 1;
}
