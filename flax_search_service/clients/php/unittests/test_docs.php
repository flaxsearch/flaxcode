<?php

# Copyright (C) 2009 Lemur Consulting Ltd
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

error_reporting(E_ALL);

class DocsTestCase extends UnitTestCase {
    var $server;
    var $dbname;
    var $db;
    var $testcount = 0;

    function __construct($server) {
        $this->server = $server;
    }
    
    function setUp() {
        $this->dbname = 'tmp'. time();
        $this->db = $this->server->createDatabase($this->dbname);
        $this->db->addField('foo', new FlaxFreeTextField(true));
    }

    function tearDown() {
        $this->db->delete();
    }
    
    function testNoDoc() {        
        try {
            $fnames = $this->db->getDocument('doc001');
            $this->fail();
        }
        catch (FlaxDocumentError $e) {
            $this->pass();
        }
    }
    
    function testAddDoc() {
        # add a doc with an ID
        $doc = array('foo' => 'bar');
        $this->db->addDocument($doc, 'doc002');
        $this->db->commit();

        # check it's been added ok
        $this->assertEqual($this->db->getDocCount(), 1);
        
        $doc2 = $this->db->getDocument('doc002');
        $this->assertEqual($doc2['foo'], array('bar'));
        
        # check that we can search for it
        $results = $this->db->searchSimple('bar');
        $this->assertEqual($results->matches_estimated, 1);

        # check we can delete it
        $this->db->deleteDocument('doc002');
        $this->db->commit();

        try {
            $this->db->getDocument('doc002');
            $this->fail();
        }
        catch (FlaxDocumentError $e) {
            $this->pass();
        }

        $results = $this->db->searchSimple('bar');
        $this->assertEqual($results->matches_estimated, 0);
    }

    function testBigDoc() {
        # add a large document
        $text =  <<<EOT
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
complexity, and their multiple consequences in many fields. His way of achieving
this was by conducting thorough, careful, sensitive, and yet transformational
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
EOT;
        $doc = array('foo' => $text);
        $this->db->addDocument($doc);
        $this->db->commit();

        # check that we can search for it
        $results = $this->db->searchSimple('derrida');
        $this->assertEqual($results->matches_estimated, 1);

        # check summarisation (is this the right place for test?)
        $results = $this->db->searchSimple('derrida', 0, 10, new FlaxSummarySettings('foo'));
        $summary = $results->results[0]->data['foo'][0];
        $this->assertTrue(count($summary) <= 500);
        $this->assertTrue(strstr($summary, '<b>Derrida</b>'));
    }
}

?>
