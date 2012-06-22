package uk.co.flax.externalcodec;

import org.apache.lucene.analysis.core.KeywordAnalyzer;
import org.apache.lucene.codecs.Codec;
import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field;
import org.apache.lucene.document.FieldType;
import org.apache.lucene.index.*;
import org.apache.lucene.search.*;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.SimpleFSDirectory;
import org.apache.lucene.util.Version;

import java.io.File;
import java.io.IOException;
import java.util.BitSet;

/**
 * Copyright (c) 2012 Lemur Consulting Ltd.
 * <p/>
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * <p/>
 * http://www.apache.org/licenses/LICENSE-2.0
 * <p/>
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
public class Example {

    /*
    So here's what we do:

    - Add a whole bunch of documents, occasionally forcing segment writes, so
      that we have a number of segments.

    - updateByQuery(Directory dir, Query query, Diff diff)
         - open dir, read segments
         - for each segment:
            - run query and get list of docids
            - create a new mergepolicy with the list of docids and diffs, and set it
              on the directory
            - forceMerge()

     UpdateFieldMergePolicy(docids, diffs)
     findMerges -> return a series of OneMerge objects combining the actual segment
                   with a faked SegmentInfoPerCommit containing the Diff


     FieldsConsumer.merge()
     FieldsConsumer.addField() -> overridden in UpdatingCodec

     */

    public static final String indexDirectory = "index/";

    public static void main(String[] args) throws IOException {
        Directory dir = new SimpleFSDirectory(new File(indexDirectory));
        //writeExampleIndex(dir);
        Query q = new TermQuery(new Term("tag", "exampletag"));
        Diff diff = new Diff();
        //querySegments(q, dir);
        //runFakeMerge(dir, q, diff);
        runUpdatingIndexWriter(dir, q, diff);
    }

    static void runUpdatingIndexWriter(Directory dir, Query query, Diff diff) throws IOException {
        IndexWriterConfig iwc = new IndexWriterConfig(Version.LUCENE_40, new KeywordAnalyzer());
        iwc.setCodec(Codec.forName("SimpleText"));
        UpdatingIndexWriter iw = new UpdatingIndexWriter(dir, iwc);
        iw.updateByQuery(query, diff);
    }

    static void runFakeMerge(Directory dir, Query query, Diff diff) throws IOException {
        IndexWriterConfig iwc = new IndexWriterConfig(Version.LUCENE_40, new KeywordAnalyzer());
        iwc.setCodec(Codec.forName("SimpleText"));
        iwc.setMergePolicy(new UpdatingCodecMergePolicy(query, diff));

        IndexWriter writer = new IndexWriter(dir, iwc);
        writer.maybeMerge();
    }

    static void querySegments(Query query, Directory dir) throws IOException {
        CompositeReader reader = DirectoryReader.open(dir);
        for (IndexReader ir : reader.getSequentialSubReaders()) {
            IndexSearcher searcher = new IndexSearcher(ir);
            final BitSet bits = new BitSet(ir.maxDoc());
            searcher.search(query, new Collector() {
                private int docBase;

                public void setScorer(Scorer scorer) {
                }

                public boolean acceptsDocsOutOfOrder() {
                     return true;
                }

                public void collect(int doc) {
                    bits.set(doc + docBase);
                   }

                public void setNextReader(AtomicReaderContext context) {
                     this.docBase = context.docBase;
                }
            });
            dump("Matching docs", bits);
        }
    }

    static void dump(String message, BitSet bits) {
        System.out.println(message);
        for (int i = bits.nextSetBit(0); i >= 0; i = bits.nextSetBit(i + 1)) {
            System.out.println(i);
        }
    }

    static void writeExampleIndex(Directory dir) throws IOException {

        IndexWriterConfig iwc = new IndexWriterConfig(Version.LUCENE_40, new KeywordAnalyzer());
        iwc.setCodec(Codec.forName("SimpleText"));

        IndexWriter writer = new IndexWriter(dir, iwc);

        FieldType ft = new FieldType();
        ft.setIndexed(true);
        for (int i = 20; i < 40; i++) {
            Document doc = new Document();
            doc.add(new Field("id", Integer.toString(i), ft));
            doc.add(new Field("tag", "exampletag", ft));
            writer.addDocument(doc);
        }

        writer.close();

    }

}
