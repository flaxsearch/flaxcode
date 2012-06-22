package uk.co.flax.rediscodec;

import org.apache.lucene.codecs.FieldsProducer;
import org.apache.lucene.index.*;
import org.apache.lucene.util.Bits;
import org.apache.lucene.util.BytesRef;
import org.jredis.RedisException;
import org.jredis.ri.alphazero.JRedisClient;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.util.Arrays;
import java.util.Comparator;

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
public class RedisUpdatingFieldsProducer extends FieldsProducer {

    private JRedisClient redis;
    private String segment;

    public RedisUpdatingFieldsProducer(SegmentReadState state) {
        this.segment = state.segmentInfo.name;
        this.redis = new JRedisClient();    // TODO: host, port, etc
    }

    @Override
    public void close() throws IOException {
        //To change body of implemented methods use File | Settings | File Templates.
    }

    @Override
    public FieldsEnum iterator() throws IOException {
        return new FieldsEnum() {

            boolean done = false;

            @Override
            public String next() throws IOException {
                if (!done) {
                    done = true;
                    return "tag";
                }
                return null;
            }

            @Override
            public Terms terms() throws IOException {
                return RedisUpdatingFieldsProducer.this.terms("tag");
            }
        };
    }

    @Override
    public Terms terms(String field) throws IOException {
        if (field != "tag")
            return null;
        return new RedisUpdatingTerms();
    }

    @Override
    public int size() throws IOException {
        return -1;
    }

    public class RedisUpdatingTerms extends Terms {

        @Override
        public TermsEnum iterator(TermsEnum reuse) throws IOException {
            return new RedisUpdatingTermsEnum();
        }

        @Override
        public Comparator<BytesRef> getComparator() throws IOException {
            return BytesRef.getUTF8SortedAsUnicodeComparator();
        }

        @Override
        public long size() throws IOException {
            return -1;
        }

        @Override
        public long getSumTotalTermFreq() throws IOException {
            return -1;
        }

        @Override
        public long getSumDocFreq() throws IOException {
            return -1;
        }

        @Override
        public int getDocCount() throws IOException {
            return -1;
        }

    }

    private class RedisUpdatingTermsEnum extends TermsEnum {

        private int[] docs;
        private BytesRef term;

        @Override
        public SeekStatus seekCeil(BytesRef text, boolean useCache) throws IOException {
            try {
                String key = segment + "_" + text.utf8ToString();
                if (!redis.exists(key)) {
                    return SeekStatus.END;      // todo iteration
                }
                byte[] data = redis.get(key);
                docs = new int[data.length / 4];
                ByteBuffer.wrap(data).asIntBuffer().get(docs);
                term = text.clone();
                return SeekStatus.FOUND;

            } catch (RedisException e) {
                throw new IOException(e);
            }
        }

        @Override
        public void seekExact(long ord) throws IOException {
            throw new UnsupportedOperationException();
        }

        @Override
        public BytesRef term() throws IOException {
            return term;
        }

        @Override
        public long ord() throws IOException {
            throw new UnsupportedOperationException();
        }

        @Override
        public int docFreq() throws IOException {
            return docs.length;
        }

        @Override
        public long totalTermFreq() throws IOException {
            return -1;
        }

        @Override
        public DocsEnum docs(Bits liveDocs, DocsEnum reuse, boolean needsFreqs) throws IOException {
            if (needsFreqs)
                return null;
            return new RedisUpdatingDocsAndPositionsEnum(liveDocs, docs);
        }

        @Override
        public DocsAndPositionsEnum docsAndPositions(Bits liveDocs, DocsAndPositionsEnum reuse, boolean needsOffsets) throws IOException {
            if (needsOffsets)
                return null;
            return new RedisUpdatingDocsAndPositionsEnum(liveDocs, docs);
        }

        @Override
        public BytesRef next() throws IOException {
            return null;
        }

        @Override
        public Comparator<BytesRef> getComparator() {
            return BytesRef.getUTF8SortedAsUnicodeComparator();
        }
    }

    private class RedisUpdatingDocsAndPositionsEnum extends DocsAndPositionsEnum {

        int[] docs;
        int current;

        public RedisUpdatingDocsAndPositionsEnum(Bits liveDocs, int[] docs) {
            this.docs = docs;
            this.current = -1;
        }

        @Override
        public int nextPosition() throws IOException {
            return -1;
        }

        @Override
        public int startOffset() throws IOException {
            return -1;
        }

        @Override
        public int endOffset() throws IOException {
            return -1;
        }

        @Override
        public BytesRef getPayload() throws IOException {
            return null;
        }

        @Override
        public boolean hasPayload() {
            return false;
        }

        @Override
        public int freq() throws IOException {
            return -1;
        }

        @Override
        public int docID() {
            if (current == -1 || current >= docs.length)
                return NO_MORE_DOCS;
            return docs[current];
        }

        @Override
        public int nextDoc() throws IOException {
            if (++current >= docs.length)
                return NO_MORE_DOCS;
            return docs[current];
        }

        @Override
        public int advance(int target) throws IOException {
            current = Arrays.binarySearch(docs, target);
            if (current < 0)
                current = -(current + 1);
            return docID();
        }
    }
}
