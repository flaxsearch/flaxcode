package uk.co.flax.rediscodec;

import org.apache.lucene.codecs.PostingsConsumer;
import org.apache.lucene.util.BytesRef;
import org.apache.lucene.util.IntsRef;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.IntBuffer;

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
public class RedisUpdatingPostingsWriter extends PostingsConsumer {

    private String segment;
    private String term;
    private IntsRef docs = new IntsRef(1024);
    private int doccount = 0;

    public RedisUpdatingPostingsWriter(String segmentname) {
        this.segment = segmentname;
    }

    @Override
    public void startDoc(int docID, int freq) throws IOException {
        // TODO: store frequencies as well?
        docs.ints[doccount] = docID;
        if (++doccount > docs.length) {
            docs.grow(docs.length * 2);
        }
    }

    @Override
    public void addPosition(int position, BytesRef payload, int startOffset, int endOffset) throws IOException {
        //To change body of implemented methods use File | Settings | File Templates.
    }

    @Override
    public void finishDoc() throws IOException {
        //To change body of implemented methods use File | Settings | File Templates.
    }

    public PostingsConsumer setTerm(BytesRef text) {
        this.term = text.utf8ToString();
        this.docs.length = 0;
        this.doccount = 0;
        return this;
    }

    public String getKey() {
        return segment + "_" + term;
    }

    public byte[] getPostings() {
        ByteBuffer bytes = ByteBuffer.allocate(doccount * 4);
        IntBuffer ib = bytes.asIntBuffer();
        ib.put(docs.ints, 0, doccount);
        return bytes.array();
    }
}
