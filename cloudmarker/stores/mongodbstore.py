"""MongoDB store plugin."""


import logging

from pymongo import MongoClient

_log = logging.getLogger(__name__)


class MongoDBStore:
    """A plugin to store records on MongoDB."""

    def __init__(self, host, port, username=None, password=None, db='gcp',
                 buffer_size=1000):
        """Create an instance of :class:`MongoDBStore` plugin.

        Arguments:
            host (str): MongoDB instance host.
            port (int): MongoDB instance port.
            username (str): MongoDB instance auth username.
            password (str): MongoDB instance auth password.
            db (str): MongoDB database name, default: ``gcp``
            buffer_size (int): Max number of records to hold in memeory for
                each record_type.

        """
        # pylint: disable=too-many-instance-attributes

        self._mongodb_host = host
        self._mongodb_port = port
        self._mongodb_username = username
        self._mongodb_password = password
        self._db = db

        self._buffer_size = buffer_size
        self._buffer = {}

        if not (username and password):
            self._client = MongoClient(host=self._mongodb_host,
                                       port=self._mongodb_port,
                                       connect=False)
        else:
            self._client = MongoClient(host=self._mongodb_host,
                                       port=self._mongodb_port,
                                       username=username,
                                       password=password,
                                       authSource=self._db,
                                       authMechanism='SCRAM-SHA-256',
                                       connect=False)

    def _flush(self, record_type, records):
        """Perform bulk insert of buffered records into MongoDB collection.

        Arguments:
          record_type (str): Collection name in MongoDB.
          records (list): List of records of type dict to store in collection.

        """
        _log.info('Inserting %i documents into collection %s ...',
                  len(records), record_type)

        self._client[self._db][record_type].insert_many(records)

        _log.info('Saved %i documents into collection %s',
                  len(records), record_type)
        del records[:]

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
        record_type = record['record_type']

        if record_type not in self._buffer:
            self._buffer[record_type] = []

        # Save the record in the buffer.
        records = self._buffer[record_type]
        records.append(record)

        # records gets more than buffer size then flush record_type records to
        # MongoDB
        if len(records) >= self._buffer_size:
            self._flush(record_type, records)

    def done(self):
        """Flush pending buffered records to MongoDB."""
        # Flush all the residual records buffers to mongodb collections
        for record_type, records in self._buffer.items():
            self._flush(record_type, records)
