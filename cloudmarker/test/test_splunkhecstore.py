"""Tests for SplunkHECToken plugin."""

import unittest
from unittest import mock

import requests

from cloudmarker.stores import splunkhecstore


class SplunkHECStoreTest(unittest.TestCase):
    """Tests for SplunkHECStore plugin."""

    def test_flush_called_once(self):
        mock_record = {'record_type': 'firewall_rule'}

        # Create a SplunkStore with buffer length 1000(default value)
        splunk_store = splunkhecstore.SplunkHECStore('', '', '', '')

        splunk_store._flush = mock.MagicMock()

        splunk_store.write(mock_record)
        splunk_store.done()

        splunk_store._flush.assert_called_once_with()

    def test_flush_called_twice(self):
        mock_record = {'record_type': 'firewall_rule'}

        # Create a zero length buffer
        splunk_store = splunkhecstore.SplunkHECStore('', '', '', '', 0)

        splunk_store._flush = mock.MagicMock()

        splunk_store.write(mock_record)
        splunk_store.done()

        self.assertEqual(splunk_store._flush.mock_calls,
                         [mock.call(), mock.call()])

    @mock.patch('cloudmarker.stores.splunkhecstore.requests.session')
    def test_flush_all_records_happy_flow(self, mock_session):
        mock_record = {'record_type': 'firewall_rule'}

        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'code': 0}

        splunk_store = splunkhecstore.SplunkHECStore('', '', '', '', 0)
        mock_session().post.return_value = mock_response

        splunk_store.write(mock_record)
        splunk_store.done()

        # Buffer will become empty when the record is successfully pushed to
        # store.
        self.assertListEqual(splunk_store._buffer, [])

    @mock.patch('cloudmarker.stores.splunkhecstore.requests.session')
    def test_flush_post_failure_no_data_loss(self, mock_session):
        mock_record = {'record_type': 'firewall_rule'}

        mock_response = mock.MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {'code': 0}

        splunk_store = splunkhecstore.SplunkHECStore('', '', '', '', 0)
        mock_session().post.return_value = mock_response

        splunk_store.write(mock_record)
        splunk_store.done()

        # In case of post request to splunk fails, buffer should not be empty.
        self.assertNotEqual(splunk_store._buffer, [])

    @mock.patch('cloudmarker.stores.splunkhecstore.requests.session')
    def test_flush_splunk_unable_to_index(self, mock_session):
        mock_record = {'record_type': 'firewall_rule'}

        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'code': 1}

        splunk_store = splunkhecstore.SplunkHECStore('', '', '', '', 0)
        mock_session().post.return_value = mock_response

        splunk_store.write(mock_record)
        splunk_store.done()

        # In case of response to post is not with code 0, then buffer shouldn't
        # be empty
        self.assertNotEqual(splunk_store._buffer, [])

    @mock.patch('cloudmarker.stores.splunkhecstore.requests.session')
    def test_flush_splunk_response_non_json(self, mock_session):
        mock_record = {'record_type': 'firewall_rule'}

        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = Exception()

        splunk_store = splunkhecstore.SplunkHECStore('', '', '', '', 0)
        mock_session().post.return_value = mock_response

        splunk_store.write(mock_record)
        splunk_store.done()

        self.assertNotEqual(splunk_store._buffer, [])

    @mock.patch('cloudmarker.stores.splunkhecstore.requests.session')
    def test_flush_post_connection_error(self, mock_session):
        mock_record = {'record_type': 'firewall_rule'}

        splunk_store = splunkhecstore.SplunkHECStore('', '', '', '', 0)
        mock_session().post.side_effect = requests.ConnectionError()

        splunk_store.write(mock_record)
        splunk_store.done()

        self.assertNotEqual(splunk_store._buffer, [])
