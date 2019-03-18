"""Tests for gcpcloud plugin."""


import copy
import unittest
from unittest import mock

from cloudmarker.clouds import gcpcloud

mock_firewall_data = {
    'kind': 'compute#firewallList',
    'items': [
        {
            'priority': 42,
            'direction': 'ingress',
            'sourceRanges': [
                '0.0.0.0',
            ]
        }
    ]
}

mock_instance_data = {
    'kind': 'compute#instanceList',
    'items': [
        {
            'status': 'str',
            'guestAccelerators': [
                {
                    'acceleratorCount': 42,
                    'acceleratorType': 'str',
                },
            ]
        }
    ],
    'id': 'str',
    'selfLink': 'str'
}


class GCPCloudTest(unittest.TestCase):
    """Tests for gcpcloud plugin."""

    @mock.patch('cloudmarker.clouds.gcpcloud.discovery')
    @mock.patch('cloudmarker.clouds.gcpcloud.service_account')
    @mock.patch('builtins.open', mock.mock_open(
        read_data='{"project_id": "foo"}'))
    def test_firewall_without_next_page_token(
            self,
            mock_service_account,
            mock_discovery):
        mock_execute = mock_discovery.build().firewalls().list().execute
        mock_execute.return_value = mock_firewall_data

        # Consume the data from the generator
        list(gcpcloud.GCPCloud('', '').read())

        mock_execute.assert_called_once_with()

    @mock.patch('cloudmarker.clouds.gcpcloud.discovery')
    @mock.patch('cloudmarker.clouds.gcpcloud.service_account')
    @mock.patch('builtins.open', mock.mock_open(
        read_data='{"project_id": "foo"}'))
    def test_firewall_with_next_page_token(
            self,
            mock_service_account,
            mock_discovery):
        mock_firewall_data_with_next_page = copy.deepcopy(mock_firewall_data)
        mock_firewall_data_with_next_page.update({'nextPageToken': 'bar'})

        mock_execute = mock_discovery.build().firewalls().list().execute
        mock_execute.side_effect = [mock_firewall_data_with_next_page,
                                    mock_firewall_data]

        # Consume the data from the generator
        list(gcpcloud.GCPCloud('', '').read())

        self.assertEqual(mock_execute.mock_calls, [mock.call(), mock.call()])

    @mock.patch('cloudmarker.clouds.gcpcloud.discovery')
    @mock.patch('cloudmarker.clouds.gcpcloud.service_account')
    @mock.patch('builtins.open', mock.mock_open(
        read_data='{"project_id": "foo"}'))
    def test_instance_without_next_page_token(
            self,
            mock_service_account,
            mock_discovery):
        mock_execute = mock_discovery.build().instances().list().execute
        mock_execute.return_value = mock_instance_data

        # Consume the data from the generator
        list(gcpcloud.GCPCloud('', '').read())

        mock_execute.assert_called_once_with()

    @mock.patch('cloudmarker.clouds.gcpcloud.discovery')
    @mock.patch('cloudmarker.clouds.gcpcloud.service_account')
    @mock.patch('builtins.open', mock.mock_open(
        read_data='{"project_id": "foo"}'))
    def test_instance_with_next_page_token(
            self,
            mock_service_account,
            mock_discovery):
        mock_instance_data_with_next_page = copy.deepcopy(mock_instance_data)
        mock_instance_data_with_next_page.update({'nextPageToken': 'bar'})

        mock_execute = mock_discovery.build().instances().list().execute
        mock_execute.side_effect = [mock_instance_data_with_next_page,
                                    mock_instance_data]

        # Consume the data from the generator
        list(gcpcloud.GCPCloud('', '').read())

        self.assertEqual(mock_execute.mock_calls, [mock.call(), mock.call()])
