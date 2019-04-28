"""Tests for SplunkHECToken plugin."""

import unittest
from unittest import mock

import requests

from cloudmarker.stores import splunkhecstore


class SplunkHECStoreTest(unittest.TestCase):
    """Tests for SplunkHECStore plugin."""

    @mock.patch('requests.session')
    def test_post_called_once(self, mock_session):
        mock_record = {'record_type': 'firewall_rule'}

        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'code': 0}
        mock_session().post.return_value = mock_response

        # Create a SplunkStore with buffer length 1000(default value)
        splunk_store = splunkhecstore.SplunkHECStore('', '', '', '')
        splunk_store.write(mock_record)
        splunk_store.done()

        mock_session().post.assert_called_once_with(mock.ANY,
                                                    headers=mock.ANY,
                                                    data=mock.ANY,
                                                    verify=mock.ANY)

    @mock.patch('requests.session')
    def test_happy_flow(self, mock_session):
        mock_record = {'record_type': 'firewall_rule'}

        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'code': 0}
        mock_session().post.return_value = mock_response

        splunk_store = splunkhecstore.SplunkHECStore('', '', '', '', 0)
        splunk_store.write(mock_record)
        splunk_store.done()

        mock_session().post.assert_called_once_with(mock.ANY,
                                                    headers=mock.ANY,
                                                    data=mock.ANY,
                                                    verify=mock.ANY)

    @mock.patch('requests.session')
    def test_post_failure_no_data_loss(self, mock_session):
        mock_record = {'record_type': 'firewall_rule'}

        mock_response = mock.MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {'code': 0}
        mock_session().post.return_value = mock_response

        splunk_store = splunkhecstore.SplunkHECStore('', '', '', '', 0)
        splunk_store.write(mock_record)
        splunk_store.done()

        mock_calls = mock_session().post.mock_calls

        post_call_signature = mock.call(mock.ANY, headers=mock.ANY,
                                        data=mock.ANY, verify=mock.ANY)
        post_call_count = mock_calls.count(post_call_signature)
        self.assertEqual(post_call_count, 2)

    @mock.patch('requests.session')
    def test_post_fail_splunk_unable_to_index(self, mock_session):
        mock_record = {'record_type': 'firewall_rule'}

        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'code': 1, 'text': 'foo'}
        mock_session().post.return_value = mock_response

        splunk_store = splunkhecstore.SplunkHECStore('', '', '', '', 0)
        splunk_store.write(mock_record)
        splunk_store.done()

        mock_calls = mock_session().post.mock_calls

        post_call_signature = mock.call(mock.ANY, headers=mock.ANY,
                                        data=mock.ANY, verify=mock.ANY)
        post_call_count = mock_calls.count(post_call_signature)
        self.assertEqual(post_call_count, 2)

    @mock.patch('requests.session')
    def test_post_fail_splunk_response_non_json(self, mock_session):
        mock_record = {'record_type': 'firewall_rule'}

        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = Exception()
        mock_session().post.return_value = mock_response

        splunk_store = splunkhecstore.SplunkHECStore('', '', '', '', 0)
        splunk_store.write(mock_record)
        splunk_store.done()

        self.assertEqual(len(mock_response.json.mock_calls), 2)

    @mock.patch('requests.session')
    def test_post_fail_raise_connection_error(self, mock_session):
        mock_record = {'record_type': 'firewall_rule'}
        mock_session().post.side_effect = requests.ConnectionError()

        splunk_store = splunkhecstore.SplunkHECStore('', '', '', '', 0)
        splunk_store.write(mock_record)
        splunk_store.done()

        self.assertEqual(len(mock_session().post.mock_calls), 2)
