package uk.co.flax.externalcodec;

import org.apache.lucene.index.*;
import org.apache.lucene.search.Collector;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.Scorer;
import org.apache.lucene.store.IOContext;

import java.io.IOException;
import java.util.ArrayList;
import java.util.BitSet;
import java.util.List;
import java.util.Map;

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
public class UpdatingCodecMergePolicy extends MergePolicy {

    private final Query query;
    private final Diff diff;

    public UpdatingCodecMergePolicy(Query query, Diff diff) {
        this.query = query;
        this.diff = diff;
    }

    @Override
    public MergeSpecification findMerges(SegmentInfos segmentInfos) throws CorruptIndexException, IOException {
        // So the idea here is to create fake merge specs for each segment that has
        // a corresponding query match.
        MergeSpecification spec = new MergeSpecification();

        for (SegmentInfoPerCommit si : segmentInfos.asList()) {
            SegmentReader reader = new SegmentReader(si, -1, new IOContext());
            BitSet docsToUpdate = getMatchingDocs(reader);
            List<SegmentInfoPerCommit> commits = new ArrayList<SegmentInfoPerCommit>();
            commits.add(si);
            commits.add(new SegmentDiff(diff, docsToUpdate));
            spec.add(new OneMerge(commits));
        }

        return spec;
    }

    private class SegmentDiff {
        public SegmentDiff(Diff diff, BitSet bits) {}
    }

    private BitSet getMatchingDocs(SegmentReader reader) throws IOException {
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

    @Override
    public MergeSpecification findForcedMerges(SegmentInfos segmentInfos, int maxSegmentCount, Map<SegmentInfoPerCommit, Boolean> segmentsToMerge) throws CorruptIndexException, IOException {
        return findMerges(segmentInfos);
    }

    @Override
    public MergeSpecification findForcedDeletesMerges(SegmentInfos segmentInfos) throws CorruptIndexException, IOException {
        return findMerges(segmentInfos);
    }

    @Override
    public void close() {
    }

    @Override
    public boolean useCompoundFile(SegmentInfos segments, SegmentInfoPerCommit newSegment) throws IOException {
        return false;
    }
}
