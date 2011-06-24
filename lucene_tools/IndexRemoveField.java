/**
*   Copyright (c) 2011 Lemur Consulting Ltd.
*
*   Licensed under the Apache License, Version 2.0 (the "License");
*   you may not use this file except in compliance with the License.
*   You may obtain a copy of the License at
*
*   http://www.apache.org/licenses/LICENSE-2.0

*   Unless required by applicable law or agreed to in writing, software
*   distributed under the License is distributed on an "AS IS" BASIS,
*   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
*   See the License for the specific language governing permissions and
*   limitations under the License.
*/

package uk.co.flax.lucene;

import java.io.File;
import java.io.IOException;
import java.util.Collection;

import org.apache.lucene.document.Document;
import org.apache.lucene.document.FieldSelector;
import org.apache.lucene.index.CorruptIndexException;
import org.apache.lucene.index.FilterIndexReader;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.IndexWriter;
import org.apache.lucene.index.IndexReader.FieldOption;
import org.apache.lucene.index.IndexWriter.MaxFieldLength;
import org.apache.lucene.store.Directory;
import org.apache.lucene.store.NIOFSDirectory;

/**
 * Class for removing fields from documents in an index. When executed from
 * the command line, arguments are:
 * 
 * <source index directory>  Directory containing source index
 * <target index directory>  Directory to contain target index
 * <field names>             Comma separated list of fields to remove
 * 
 * Note that terms are not changed - it is equivalent to changing the 'stored'
 * property of a field from true to false.
 * 
 * @author tomw@flax.co.uk
 */
public class IndexRemoveField {

	// sub-class of FilterIndexReader for removing document fields
	private static class FieldRemoveReader extends FilterIndexReader {

		// collection of fields to remove
		private String[] fields;
		
		// how many documents processed so far
		private int count;
		
		/**
		 * Create an FieldRemoveReader, wrapping the given IndexReader to remove
		 * the named fields.
		 * 
		 * @param reader The IndexReader to wrap
		 * @param fields Fields to remove
		 */
		public FieldRemoveReader(IndexReader reader, String... fields) {
			super(reader);
			this.fields = fields;
			count = 0;
		}
		
		/**
		 * @return how many documents have been processed so far
		 */
		public int getCount() {
			return count;
		}

	    @Override
	    public IndexReader[] getSequentialSubReaders() {
	      return null;
	    }
		
		@Override
		public Document document(int n) throws CorruptIndexException, IOException {
			if (count % 10000 == 0) {
				System.out.println();
				System.out.print("Progress: " + count + " ");
			}
			if (count % 500 == 0) {
				System.out.print(".");
			}
			count++;
			return this.document(n, null);
		}
		
		@Override
		public Document document(int n, FieldSelector fieldSelector) throws CorruptIndexException, IOException {
			Document doc = super.document(n, fieldSelector);
			for (String field : fields) {
				doc.removeFields(field);
			}
			return doc;
		}
		
	}
	
	// report on whether fields exist in the given reader, and return result
	@SuppressWarnings("unchecked")
	private static boolean hasFields(IndexReader reader, String... fields) {
		boolean value = true;
		Collection<String> fieldNames = reader.getFieldNames(FieldOption.ALL);
		for (String field : fields) {
			if (! fieldNames.contains(field)) {
				System.out.println("Field " + field + " not recognized");
				value = false;
			}
		}
		return value;
	}
	
	/**
	 * Remove fields from documents in an index.
	 * 
	 * @param args Command line arguments
	 * @throws IOException
	 */
	public static void main(String[] args) throws IOException {
		// parse command line arguments
		if (args.length < 3) {
			System.out.println("Usage: java uk.co.flax.IndexRemoveField <source index dir> <target index dir> <field1,field2,...>");
			return;
		}
		String sourceIndex = args[0];
		String targetIndex = args[1];
		String fields = args[2];
		
		// open an IndexReader for the source index (read-only)
		Directory sourceDir = new NIOFSDirectory(new File(sourceIndex));
		IndexReader reader = IndexReader.open(sourceDir, true);
		
		// open an IndexWriter for the target index (with a null Analyzer)
		Directory targetDir = new NIOFSDirectory(new File(targetIndex));
		//IndexWriterConfig config = new IndexWriterConfig(Version.LUCENE_31, null);
		IndexWriter writer = new IndexWriter(targetDir, null, MaxFieldLength.UNLIMITED);
		
		// add indexes from a wrapped IndexReader to the IndexWriter
		try {
			String[] fieldNames = fields.split(",");
			if (hasFields(reader, fieldNames)) {
				System.out.print("Removing fields from " + reader.numDocs() + " documents");
				FieldRemoveReader removeReader = new FieldRemoveReader(reader, fieldNames);
				writer.addIndexes(new IndexReader[] { removeReader });
				System.out.println();
				System.out.println("Complete: " + removeReader.getCount());
			}
		} finally {
			reader.close();
			writer.close();
		}
	}
}
