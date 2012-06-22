package uk.co.flax.rediscodec;

import junit.framework.Assert;
import org.apache.lucene.analysis.core.KeywordAnalyzer;
import org.apache.lucene.codecs.PostingsFormat;
import org.apache.lucene.codecs.lucene40.Lucene40Codec;
import org.apache.lucene.codecs.lucene40.Lucene40PostingsFormat;
import org.apache.lucene.document.Document;
import org.apache.lucene.document.Field;
import org.apache.lucene.document.FieldType;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexWriterConfig;
import org.apache.lucene.index.Term;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.TermQuery;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.SimpleFSDirectory;
import org.apache.lucene.util.Version;
import org.jredis.RedisException;
import org.jredis.ri.alphazero.JRedisClient;
import org.junit.Before;
import org.junit.Test;

import java.io.File;
import java.io.IOException;

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

/**
 * This is the meat of the idea.  We define a new per-field Codec that
 * uses the RedisUpdatingPostingsFormat for the 'tag' field, and standard
 * Lucene40 for all other fields.  We then add a few documents, and make
 * sure that they're searchable.
 *
 * Then we update one of the documents, changing its tag from 'exampletag'
 * to 'updatedtag'.  We re-run the searches, and show that the number of
 * hits from each has changed accordingly.  Et voila, an updateable field!
 */
public class TestCodec {

    public static final String indexdir = "index/";

    @Before
    public void setUp() throws IOException, RedisException {
        Runtime.getRuntime().exec("rm -rf " + indexdir);
        JRedisClient redis = new JRedisClient();
        redis.del("_0_exampletag", "_0_updatedtag");
    }

    @Test
    public void testUpdateCodec() throws IOException {

        Directory dir = new SimpleFSDirectory(new File(indexdir));
        writeTestIndex(dir);

        Query q1 = new TermQuery(new Term("tag", "exampletag"));
        Query q2 = new TermQuery(new Term("tag", "updatedtag"));

        IndexSearcher searcher = new IndexSearcher(DirectoryReader.open(dir));

        Assert.assertEquals(10, searcher.search(q1, 1).totalHits);
        Assert.assertEquals(0, searcher.search(q2, 1).totalHits);

        Diff diff = new Diff();
        diff.addTerm(new Term("tag", "updatedtag"));
        diff.deleteTerm(new Term("tag", "exampletag"));

        Query updatequery = new TermQuery(new Term("id", "4"));

        Updater.updateByQuery(dir, updatequery, diff);

        Assert.assertEquals(1, searcher.search(q2, 1).totalHits);
        Assert.assertEquals(9, searcher.search(q1, 1).totalHits);


    }

    static void writeTestIndex(Directory dir) throws IOException {

        IndexWriterConfig iwc = new IndexWriterConfig(Version.LUCENE_40, new KeywordAnalyzer());
        iwc.setCodec(new MockCodec());

        IndexWriter writer = new IndexWriter(dir, iwc);

        FieldType ft = new FieldType();
        ft.setIndexed(true);
        for (int i = 0; i < 10; i++) {
            Document doc = new Document();
            doc.add(new Field("id", Integer.toString(i), ft));
            doc.add(new Field("tag", "exampletag", ft));
            writer.addDocument(doc);
        }

        writer.close();

    }

    public static class MockCodec extends Lucene40Codec {
        final PostingsFormat lucene40 = new Lucene40PostingsFormat();
        final PostingsFormat redis = new RedisUpdatingPostingsFormat();

        @Override
        public PostingsFormat getPostingsFormatForField(String field) {
            if (field.equals("tag")) {
                return redis;
            } else {
                return lucene40;
            }
        }
    }

}
