package uk.co.flax.rediscodec;

import org.apache.lucene.index.*;
import org.apache.lucene.search.Collector;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.Scorer;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.IOContext;
import org.jredis.RedisException;
import org.jredis.ri.alphazero.JRedisClient;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.IntBuffer;
import java.util.Arrays;
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
public class Updater {

    public static void updateByQuery(Directory dir, Query updatequery, Diff diff) throws IOException {

        // Do the segment dance - for each segment, run the query and get the relevant
        // docids to update.
        SegmentInfos segments = new SegmentInfos();
        segments.read(dir);

        for (SegmentInfoPerCommit si : segments) {
            SegmentReader reader = new SegmentReader(si, 1, new IOContext());
            BitSet docsToUpdate = getMatchingDocs(updatequery, reader);
            updateSegment(si.info.name, docsToUpdate, diff);
        }

    }

    private static void updateSegment(String segment, BitSet docs, Diff diff) throws IOException {
        JRedisClient redis = new JRedisClient();
        try {
            for (Term add : diff.getAdds()) {
                String key = segment + "_" + add.text();
                if (!redis.exists(key)) {
                    // New key - just add it with the current bitset
                    //int[] docset = new int[docs.cardinality()];
                    ByteBuffer bytes = ByteBuffer.allocate(docs.cardinality() * 4);
                    IntBuffer docset = bytes.asIntBuffer();
                    for (int i = docs.nextSetBit(0), j = 0; i >= 0; i = docs.nextSetBit(i + 1), j++) {
                        docset.put(j, i);
                    }
                    redis.set(key, bytes.array());
                }
                else {
                    byte[] orig = redis.get(key);
                    int[] origpostings = new int[orig.length / 4];
                    int[] newpostings = new int[origpostings.length + docs.cardinality()];
                    ByteBuffer.wrap(orig).asIntBuffer().get(origpostings);
                    //ByteBuffer buffer = ByteBuffer.allocate(orig.length + docs.cardinality() * 4);
                    //IntBuffer postings = buffer.asIntBuffer();
                    int spos = 0, dpos = 0, ndoc = -1;
                    while ((ndoc = docs.nextSetBit(ndoc + 1)) >= 0) {
                        if (spos >= origpostings.length) {
                            newpostings[dpos++] = ndoc;
                        }
                        else {
                            int upto = Arrays.binarySearch(origpostings, ndoc);
                            if (upto < 0) {
                                upto = -(upto + 1);
                                System.arraycopy(origpostings, spos, newpostings, dpos, upto - spos);
                                dpos += upto - spos;
                                spos = upto;
                                newpostings[dpos++] = ndoc;
                            }
                            else {
                                // We already exist in this document, so just copy the old stuff up
                                System.arraycopy(origpostings, spos, newpostings, dpos, upto - spos);
                                dpos += upto - spos;
                                spos = upto;
                            }
                        }
                    }
                    ByteBuffer bb = ByteBuffer.allocate(newpostings.length * 4);
                    bb.asIntBuffer().put(newpostings);
                    redis.set(key, bb.array());
                }
            }
            for (Term del : diff.getDeletes()) {
                String key = segment + "_" + del.text();
                if (!redis.exists(key)) {
                    continue;
                }
                byte[] orig = redis.get(key);
                int[] origpostings = new int[orig.length / 4];
                int[] newpostings = new int[origpostings.length - docs.cardinality()];
                ByteBuffer.wrap(orig).asIntBuffer().get(origpostings);

                int spos = 0, dpos = 0, ndoc = -1;
                while ((ndoc = docs.nextSetBit(ndoc + 1)) >= 0) {
                    if (spos >= origpostings.length)
                        break;
                    while (origpostings[spos++] < ndoc) {
                        newpostings[dpos++] = origpostings[spos];
                    }
                    spos++;
                }
                if (spos < origpostings.length) {
                    System.arraycopy(origpostings, spos, newpostings, dpos, origpostings.length - spos);
                }
                ByteBuffer bb = ByteBuffer.allocate(newpostings.length * 4);
                bb.asIntBuffer().put(newpostings);
                redis.set(key, bb.array());
            }
        } catch (RedisException e) {
            throw new IOException(e);
        }
    }

    private static BitSet getMatchingDocs(Query query, SegmentReader reader) throws IOException {
        IndexSearcher searcher = new IndexSearcher(reader);
        final BitSet bits = new BitSet(reader.maxDoc());
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
        return bits;
    }
}
