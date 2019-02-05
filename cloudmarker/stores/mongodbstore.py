"""MongoDB store plugin."""


import logging

from pymongo import MongoClient, errors

_log = logging.getLogger(__name__)


class MongoDBStore:
    """A plugin to store records on MongoDB."""

    def __init__(self, db, username, password, host, port=27017,
                 buffer_size=1000, **kwargs):
        """Create an instance of :class:`MongoDBStore` plugin.

        It will use the default port for mongodb 27017 if not specified.
        The Authentication scheme will be negotiated by MongoDB and the client
        for v4.0+ to SCRAM-SHA-1 or SCRAM-SHA-256 by default aftere
        negotiation.

        Arguments:
            db (str): name of the database
            username (str): username for the database
            password (str): password for username to authenticate with the db
            host (str): hostname for the DB server
            port (int): port for mongoDB is listening, defaults to 27017
            buffer_size (int): max buffer before flushing to db
            kwargs (dict): Additional args
                * models - List of classes for validator and enforcement
                    requirements.
        """
        self._client = MongoClient(
            host=host,
            port=port,
            username=username,
            password=password
        )

        self._db = self._client[db]

        # Create collections if they don't exist based on the document
        # restrictions the users want to have.
        #
        # The collection creation, where the models objects specified,
        # are done with the following way. The object specified must
        # have the following functions:
        #
        #     collection(): returns the name of the collection
        #     validator(): returns a valid string with $jsonSchema that
        #         contains all the validation properties as specified in
        #         the mongodb docs.
        #     enforce(): returns one of the strings ``error`` or
        #         ``warn``. This will be used to define the error level
        #         for when the schema validation fails. ``error`` will
        #         raise an error while ``warn`` will log that violation
        #         in the db server logs.
        for model in kwargs.get('models', []):
            if model.collection() not in self._db.list_collection_names():
                self._db.create_collection(
                    model.collection(),
                    validator=model.validator(),
                    validationAction=model.enforce()
                )

        self._buffer = {}
        self._buffer_size = buffer_size

    def _flush(self, record_type, records):
        """Perform bulk insert of buffered records into MongoDB collection.

        Arguments:
          record_type (str): Collection name in MongoDB.
          records (list): List of records of type dict to store in collection.

        """
        _log.info('Inserting %i documents into collection %s ...',
                  len(records), record_type)

        try:
            # Making the bulk insert ordered=False, to make sure that all
            # of the documents are tried to be inserted. In the default
            # config, it will fail after the first error
            res = self._db[record_type].insert_many(records, ordered=False)
            _log.info('Saved %i out of %i documents into collection: %s',
                      len(res.inserted_ids), len(records), record_type)

            del records[:]
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

        # Close the MongoDB connection when done is called as this will be the
        # last call to the store plugin.
        self._client.close()
