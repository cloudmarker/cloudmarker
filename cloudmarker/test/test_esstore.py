"""Tests for EsStore plugin."""

import unittest
from unittest import mock

from elasticsearch import ElasticsearchException

from cloudmarker.stores import esstore


class EsStoreTest(unittest.TestCase):
    """Tests for EsStore plugin."""

    @mock.patch('cloudmarker.stores.esstore.Elasticsearch.bulk')
    def test_happy_flow(self, mock_bulk):
        mock_record = {'record_type': 'firewall_rule'}
        mock_bulk_response = {
            'errors': False,
            'items': [
                {'index': {'status': 200}}
            ]
        }

        mock_bulk.return_value = mock_bulk_response

        es_store = esstore.EsStore()
        es_store.write(mock_record)
        es_store.done()

        mock_bulk.assert_called_once_with(mock.ANY)

    @mock.patch('cloudmarker.stores.esstore.Elasticsearch.bulk')
    def test_exception_flow(self, mock_bulk):
        mock_record = {'record_type': 'firewall_rule'}
        mock_bulk.side_effect = ElasticsearchException()

        es_store = esstore.EsStore()
        es_store.write(mock_record)
        es_store.done()

        mock_bulk.assert_called_once_with(mock.ANY)

    @mock.patch('cloudmarker.stores.esstore.Elasticsearch.bulk')
    def test_bulk_response_error(self, mock_bulk):
        mock_record = {'record_type': 'firewall_rule'}
        mock_bulk_response = {
            'errors': True,
            'items': [
                {
                    'index': {
                        'status': 500,
                        '_id': 'foo'
                    }
                }
            ]
        }

        mock_bulk.return_value = mock_bulk_response

        es_store = esstore.EsStore()
        es_store.write(mock_record)
        es_store.done()

        mock_bulk.assert_called_once_with(mock.ANY)

    @mock.patch('cloudmarker.stores.esstore.Elasticsearch.bulk')
    def test_bulk_response_error_item_200(self, mock_bulk):
        mock_record = {'record_type': 'firewall_rule'}
        mock_bulk_response = {
            'errors': True,
            'items': [
                {
                    'index': {
                        'status': 200,
                        '_id': 'foo'
                    }
                }
            ]
        }

        mock_bulk.return_value = mock_bulk_response

        es_store = esstore.EsStore()
        es_store.write(mock_record)
        es_store.done()

        mock_bulk.assert_called_once_with(mock.ANY)
