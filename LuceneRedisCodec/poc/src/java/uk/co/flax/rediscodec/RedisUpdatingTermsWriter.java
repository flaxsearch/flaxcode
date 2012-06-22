package uk.co.flax.rediscodec;

import org.apache.lucene.codecs.PostingsConsumer;
import org.apache.lucene.codecs.TermStats;
import org.apache.lucene.codecs.TermsConsumer;
import org.apache.lucene.util.BytesRef;
import org.jredis.RedisException;
import org.jredis.ri.alphazero.JRedisClient;

import java.io.IOException;
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
public class RedisUpdatingTermsWriter extends TermsConsumer {

    private RedisUpdatingPostingsWriter writer;
    private JRedisClient redis;

    public RedisUpdatingTermsWriter(JRedisClient redis, String segmentname) {
        this.redis = redis;
        this.writer = new RedisUpdatingPostingsWriter(segmentname);
    }

    @Override
    public PostingsConsumer startTerm(BytesRef text) throws IOException {
        return writer.setTerm(text);
    }

    @Override
    public void finishTerm(BytesRef text, TermStats stats) throws IOException {
        // Write term to redis!
        try {
            redis.set(writer.getKey(), writer.getPostings());
        } catch (RedisException e) {
            throw new IOException(e);
        }

    }

    @Override
    public void finish(long sumTotalTermFreq, long sumDocFreq, int docCount) throws IOException {
        //To change body of implemented methods use File | Settings | File Templates.
    }

    @Override
    public Comparator<BytesRef> getComparator() throws IOException {
        return BytesRef.getUTF8SortedAsUnicodeComparator();
    }
}
