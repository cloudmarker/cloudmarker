"""MongoDB store plugin."""


import logging

from pymongo import MongoClient, errors

_log = logging.getLogger(__name__)


class MongoDBStore:
    """A plugin to store records on MongoDB."""

    def __init__(self, host='localhost', port=27017, db='cloudmarker',
                 collection='cloudmarker', username=None, password=None,
                 buffer_size=1000):
        """Create an instance of :class:`MongoDBStore` plugin.

        It will use the default port for mongodb 27017 if not specified.
        The Authentication scheme will be negotiated by MongoDB and the client
        for v4.0+ to SCRAM-SHA-1 or SCRAM-SHA-256 by default aftere
        negotiation.

        Arguments:
            host (str): hostname for the DB server
            port (int): port for mongoDB is listening
            db (str): name of the database
            collection (str): Name of MongoDB collection.
            username (str): username for the database
            password (str): password for username to authenticate with the db
            buffer_size (int): maximum number of records to buffer
        """
        self._client = MongoClient(
            host=host,
            port=port,
            username=username,
            password=password
        )

        self._collection = self._client[db][collection]
        self._buffer = []
        self._buffer_size = buffer_size

    def _flush(self):
        """Perform bulk insert of buffered records into MongoDB collection.

        Arguments:
          records (list): List of records of type dict to store in collection.

        """
        _log.info('Inserting %d records into collection %s ...',
                  len(self._buffer), self._collection.name)

        try:
            # Making the bulk insert ordered=False, to make sure that all
            # of the documents are tried to be inserted. In the default
            # config, it will fail after the first error
            res = self._collection.insert_many(self._buffer, ordered=False)
            _log.info('Inserted %d of %d documents into collection %s',
                      len(res.inserted_ids), len(self._buffer),
                      self._collection.name)

            del self._buffer[:]
        except errors.BulkWriteError as bwe:
            _log.error('Failed to write records with error %s', bwe)

    def write(self, record):
        """Write JSON records to the MongoDB collections.

        This method is called once for every ``record`` read from a
        cloud. This method saves the records into in-memory buffers. A
        separate buffer is created and maintained for each record type
        found in ``record['record_type']``. When the number of records
        in a buffer equals or exceeds the buffer size specified while
        creating an instance of :class:`MongoDBStore` plugin, the
        records in the buffer are flushed (saved into a MongoDB
        collection).

        The record type, i.e., ``record['record_type']`` is used to
        determine the collection name in MongoDB.

        Arguments:
            record (dict): Data to save in MongoDB.

        """
        # Save the record in the buffer.
        self._buffer.append(record)

        # If we have more records than self._buffer_size, flush the
        # records to MongoDB.
        if len(self._buffer) >= self._buffer_size:
            self._flush()

    def done(self):
        """Flush pending records to MongoDB and close MongoDB client."""
        self._flush()
        self._client.close()
