"""Tests for mongodbstore plugin."""


import unittest
from unittest import mock

from pymongo import errors

from cloudmarker.stores import mongodbstore


class MongoDBStoreTest(unittest.TestCase):
    """Tests for mongodbstore plugin."""

    @mock.patch('cloudmarker.stores.mongodbstore.MongoClient')
    def test_write_without_flush(self, mock_client):
        # Set buffer size of 3.
        store = mongodbstore.MongoDBStore(buffer_size=3)

        # But insert only 2 records.
        for i in range(2):
            record = {'record_type': 'foo', 'i': i}
            store.write(record)

        # Verify that buffer is not being flushed via client.
        mock_method = mock_client()['fake_db']['fake_record_type'].insert_many
        mock_method.assert_not_called()

    @mock.patch('cloudmarker.stores.mongodbstore.MongoClient')
    def test_write_with_flush(self, mock_client):
        # Set buffer size of 3.
        store = mongodbstore.MongoDBStore(buffer_size=3)

        # Then insert 3 records.
        for i in range(3):
            record = {'record_type': 'foo', 'i': i}
            store.write(record)

        # Verify that buffer is being flushed via client.
        mock_method = mock_client()['fake_db']['fake_record_type'].insert_many
        mock_method.assert_called_once_with(mock.ANY, ordered=mock.ANY)

    @mock.patch('cloudmarker.stores.mongodbstore.MongoClient')
    def test_done(self, mock_client):
        # Write only one record to store with default buffer size.
        store = mongodbstore.MongoDBStore()
        store.write({'record_type': 'foo', 'i': 0})

        # Call store's done(), so that it flushes the pending buffer.
        store.done()

        # Verify that the pending buffer is flushed via client.
        mock_method = mock_client()['fake_db']['fake_record_type'].insert_many
        mock_method.assert_called_once_with(mock.ANY, ordered=mock.ANY)

        # Verify that client is being closed.
        mock_method = mock_client().close
        mock_method.assert_called_once_with()

    @mock.patch('cloudmarker.stores.mongodbstore.MongoClient')
    def test_bulk_write_error(self, mock_client):

        # Configure the mock client such that it raises BulkWriteError
        # on insertion of records.
        mock_method = mock.Mock(side_effect=errors.BulkWriteError(None))
        mock_client()['fake_db']['fake_record_type'].insert_many = mock_method

        # Ensure that the error is handled gracefully without a crash.
        store = mongodbstore.MongoDBStore()
        store.write({'record_type': 'foo', 'i': 0})
        store.done()
