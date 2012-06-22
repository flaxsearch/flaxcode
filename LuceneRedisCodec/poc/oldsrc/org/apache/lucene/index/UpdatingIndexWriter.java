package org.apache.lucene.index;

import org.apache.lucene.codecs.FieldsConsumer;
import org.apache.lucene.search.Collector;
import org.apache.lucene.search.IndexSearcher;
import org.apache.lucene.search.Query;
import org.apache.lucene.search.Scorer;
import org.apache.lucene.store.CompoundFileDirectory;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.IOContext;
import uk.co.flax.rediscodec.Diff;

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
public class UpdatingIndexWriter extends IndexWriter {
    /**
     * Constructs a new IndexWriter per the settings given in <code>conf</code>.
     * Note that the passed in {@link org.apache.lucene.index.IndexWriterConfig} is
     * privately cloned; if you need to make subsequent "live"
     * changes to the configuration use {@link #getConfig}.
     * <p/>
     *
     * @param d    the index directory. The index is either created or appended
     *             according <code>conf.getOpenMode()</code>.
     * @param conf the configuration settings according to which IndexWriter should
     *             be initialized.
     * @throws org.apache.lucene.index.CorruptIndexException
     *                             if the index is corrupt
     * @throws org.apache.lucene.store.LockObtainFailedException
     *                             if another writer has this index open (<code>write.lock</code>
     *                             could not be obtained)
     * @throws java.io.IOException if the directory cannot be read/written to, or if it does not
     *                             exist and <code>conf.getOpenMode()</code> is
     *                             <code>OpenMode.APPEND</code> or if there is any other low-level
     *                             IO error
     */
    public UpdatingIndexWriter(Directory d, IndexWriterConfig conf) throws IOException {
        super(d, conf);
    }

    public void updateByQuery(Query query, Diff diff) throws IOException {

        Directory directory = getReader().directory();

        for (SegmentInfoPerCommit si : this.segmentInfos) {
            SegmentReader reader = new SegmentReader(si, -1, new IOContext());
            BitSet docsToUpdate = getMatchingDocs(query, reader);

            FieldInfos fis = getFieldInfos(si.info);

            SegmentWriteState writeState = new SegmentWriteState(this.infoStream, directory, si.info, fis, -1, null, IOContext.DEFAULT);
            FieldsConsumer consumer = si.info.getCodec().postingsFormat().fieldsConsumer(writeState);

            MergeState mergeState = new MergeState();
            mergeState.fieldInfos = fis;
            mergeState.segmentInfo = si.info;
            consumer.merge(mergeState, reader.fields());
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

    // Shamelessly copied from parent...
    private FieldInfos getFieldInfos(SegmentInfo info) throws IOException {
        Directory cfsDir = null;
        try {
            if (info.getUseCompoundFile()) {
                cfsDir = new CompoundFileDirectory(info.dir,
                        IndexFileNames.segmentFileName(info.name, "", IndexFileNames.COMPOUND_FILE_EXTENSION),
                        IOContext.READONCE,
                        false);
            } else {
                cfsDir = info.dir;
            }
            return info.getCodec().fieldInfosFormat().getFieldInfosReader().read(cfsDir,
                    info.name,
                    IOContext.READONCE);
        } finally {
            if (info.getUseCompoundFile() && cfsDir != null) {
                cfsDir.close();
            }
        }
    }
}
