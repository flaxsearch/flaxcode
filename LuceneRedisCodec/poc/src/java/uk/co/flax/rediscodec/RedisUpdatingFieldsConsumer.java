package uk.co.flax.rediscodec;

import org.apache.lucene.codecs.FieldsConsumer;
import org.apache.lucene.codecs.TermsConsumer;
import org.apache.lucene.index.FieldInfo;
import org.apache.lucene.index.SegmentWriteState;
import org.jredis.ri.alphazero.JRedisClient;

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
public class RedisUpdatingFieldsConsumer extends FieldsConsumer {

    private String segmentName;
    private JRedisClient redis;

    public RedisUpdatingFieldsConsumer(SegmentWriteState state) {
        segmentName = state.segmentInfo.name;
        redis = new JRedisClient();     // TODO: host, port, etc!
    }

    @Override
    public TermsConsumer addField(FieldInfo field) throws IOException {
        return new RedisUpdatingTermsWriter(redis, segmentName);
    }

    @Override
    public void close() throws IOException {
        //To change body of implemented methods use File | Settings | File Templates.
    }
}
