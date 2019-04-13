"""Elasticsearch store plugin."""


import json
import logging

from elasticsearch import Elasticsearch, ElasticsearchException

_log = logging.getLogger(__name__)


class EsStore:
    """Elasticsearch adapter to index cloud data in Elasticsearch."""

    def __init__(self, host='localhost', port=9200, index='cloudmarker',
                 buffer_size=5000000):
        """Create an instance of :class:`EsStore` plugin.

        The plugin uses the default port for Elasticsearch if not
        specified.

        The ``buffer_size`` for the plugin is the value for the maximum
        number of bytes of data to be sent in a bulk API request to
        Elasticsearch.

        Arguments:
            host (str): Elasticsearch host
            port (int): Elasticsearch port
            index (str): Elasticsearch index
            buffer_size (int): Maximum number of bytes of data to hold
                in the in-memory buffer.

        """
        self._es = Elasticsearch([{'host': host, 'port': port}])
        self._index = index
        self._buffer_size = buffer_size
        self._buffer = ''
        self._cur_buffer_size = 0

    # TODO: Add method to create mapping for efficient indexing of data.

    # TODO: Add method to prune old data.

    # TODO: Add support for multiple indexes

    def _doc_index_body(self, doc, doc_id=None):
        """Create the body for a bulk insert API call to Elasticsearch.

        Arguments:
            doc (dict): Document
            doc_id: Document ID

        Returns:
            (str): Request body corresponding to the ``doc``.

        """
        action_def = {
            'index': {
                '_index': self._index,
                '_id': doc_id
            }
        }
        src_def = doc
        return json.dumps(action_def) + '\n' + json.dumps(src_def) + '\n'

    def _flush(self):
        """Bulk insert buffered records into Elasticserach."""
        try:
            resp = self._es.bulk(self._buffer)
        except ElasticsearchException as e:
            # Handles exceptions of all types defined here.
            # https://github.com/elastic/elasticsearch-py/blob/master/elasticsearch/exceptions.py
            _log.error('Bulk Index Error: %s: %s', type(e).__name__, e)
            return

        # Read and parse the response.
        items = resp['items']
        records_sent = len(items)
        fail_count = 0

        # If response code for an item is not 2xx, increment the count of
        # failed insertions.
        if resp['errors']:
            for item in items:
                if not 199 < item['index']['status'] < 300:
                    fail_count += 1
                    _log.debug('Failed to insert record; ID: %s',
                               item['index']['_id'])
            _log.error('Failed to write %d records', fail_count)

        _log.info('Indexed %d records', records_sent - fail_count)

        # Reset the buffer.
        self._cur_buffer_size = 0
        self._buffer = ''

    def write(self, record):
        """Write JSON records to the Elasticsearch index.

        Flush the buffer by saving its content to Elasticsearch  when
        the buffer size exceeds the configured size.

        Arguments:
            record (dict): Data to save to Elasticsearch.

        """
        es_record = self._doc_index_body(record)    # TODO: Send valid doc ID
        es_record_bytes = len(es_record)
        if (self._cur_buffer_size and
                es_record_bytes + self._cur_buffer_size > self._buffer_size):
            self._flush()
        else:
            self._buffer += es_record
            self._cur_buffer_size += es_record_bytes

    def done(self):
        """Flush pending records to Elasticsearch."""
        if self._cur_buffer_size:
            self._flush()
