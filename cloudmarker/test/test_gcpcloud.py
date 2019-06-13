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

mock_zones_data = {
    'items': [
        {
            'name': 'foozone'
        }
    ]
}

mock_projects_dict = {
    'projects': [
        {
            'projectId': 'fooproject',
            'name': 'fooproject'
        }
    ]
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

        mock_project_execute = mock_discovery.build().projects().list().execute
        mock_project_execute.return_value = mock_projects_dict

        # Consume the data from the generator
        list(gcpcloud.GCPCloud('').read())

        mock_execute.assert_called_once_with()
        mock_project_execute.assert_called_once_with()

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

        mock_projects_data_with_next_page = copy.deepcopy(mock_projects_dict)
        mock_projects_data_with_next_page.update({'nextPageToken': 'bar'})

        mock_execute = mock_discovery.build().firewalls().list().execute
        mock_execute.side_effect = [mock_firewall_data_with_next_page,
                                    mock_firewall_data] * 2

        mock_project_execute = mock_discovery.build().projects().list().execute
        mock_project_execute.side_effect = [mock_projects_data_with_next_page,
                                            mock_projects_dict]

        # Consume the data from the generator
        list(gcpcloud.GCPCloud('').read())

        self.assertEqual(mock_execute.mock_calls,
                         [mock.call(), mock.call()] * 2)
        self.assertEqual(mock_project_execute.mock_calls,
                         [mock.call(), mock.call()])

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

        mock_zone_execute = mock_discovery.build().zones().list().execute
        mock_zone_execute.return_value = mock_zones_data

        mock_project_execute = mock_discovery.build().projects().list().execute
        mock_project_execute.return_value = mock_projects_dict

        # Consume the data from the generator
        list(gcpcloud.GCPCloud('').read())

        mock_execute.assert_called_once_with()
        mock_zone_execute.assert_called_once_with()
        mock_project_execute.assert_called_once_with()

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

        mock_zones_data_with_next_page = copy.deepcopy(mock_zones_data)
        mock_zones_data_with_next_page.update({'nextPageToken': 'bar'})

        mock_projects_data_with_next_page = copy.deepcopy(mock_projects_dict)
        mock_projects_data_with_next_page.update({'nextPageToken': 'bar'})

        mock_execute = mock_discovery.build().instances().list().execute
        mock_execute.side_effect = [mock_instance_data_with_next_page,
                                    mock_instance_data] * 4

        mock_zone_execute = mock_discovery.build().zones().list().execute
        mock_zone_execute.side_effect = [mock_zones_data_with_next_page,
                                         mock_zones_data] * 2

        mock_project_execute = mock_discovery.build().projects().list().execute
        mock_project_execute.side_effect = [mock_projects_data_with_next_page,
                                            mock_projects_dict]

        # Consume the data from the generator
        list(gcpcloud.GCPCloud('').read())

        self.assertEqual(mock_execute.mock_calls,
                         [mock.call(), mock.call()] * 4)
        self.assertEqual(mock_zone_execute.mock_calls,
                         [mock.call(), mock.call()] * 2)
        self.assertEqual(mock_project_execute.mock_calls,
                         [mock.call(), mock.call()])

    def _patch(self, target):
        patcher = mock.patch('cloudmarker.clouds.gcpcloud.' + target)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def setUp(self):
        patcher = mock.patch('builtins.open',
                             mock.mock_open(read_data='{"project_id": "foo"}'))
        self.addCleanup(patcher.stop)
        patcher.start()

        self._patch('service_account')
        self._mock_discovery = self._patch('discovery')

    def test_firewall_single_allowed_rule(self):
        mock_firewall_dict = {
            'items': [
                {
                    'allowed': [{}]
                }
            ]
        }
        m = self._mock_discovery
        m.build().projects().list().execute.return_value = mock_projects_dict
        m.build().firewalls().list().execute.return_value = mock_firewall_dict
        records = list(gcpcloud.GCPCloud('').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['com']['access'], 'allow')

    def test_firewall_multiple_allowed_rules(self):
        mock_firewall_dict = {
            'items': [
                {
                    'allowed': [{}, {}]
                }
            ]
        }
        m = self._mock_discovery
        m.build().projects().list().execute.return_value = mock_projects_dict
        m.build().firewalls().list().execute.return_value = mock_firewall_dict
        records = list(gcpcloud.GCPCloud('').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]['com']['access'], 'allow')
        self.assertEqual(records[1]['com']['access'], 'allow')

    def test_firewall_zero_allowed_rules(self):
        mock_firewall_dict = {
            'items': [
                {
                    'allowed': []
                }
            ]
        }
        m = self._mock_discovery
        m.build().projects().list().execute.return_value = mock_projects_dict
        m.build().firewalls().list().execute.return_value = mock_firewall_dict
        records = list(gcpcloud.GCPCloud('').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]
        self.assertEqual(len(records), 0)

    def test_firewall_allowed_and_denied_rules_both_present(self):
        mock_firewall_dict = {
            'items': [
                {
                    'allowed': [{}],
                    'denied': [{}],
                }
            ]
        }

        # We do not expect both 'allowed' and 'denied' rules to be
        # present in the same firewall item but we are making sure here
        # that if they were to be present together, we are still able to
        # handle it in a sensible manner.

        m = self._mock_discovery
        m.build().projects().list().execute.return_value = mock_projects_dict
        m.build().firewalls().list().execute.return_value = mock_firewall_dict
        records = list(gcpcloud.GCPCloud('').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]['com']['access'], 'allow')
        self.assertEqual(records[1]['com']['access'], 'deny')

    def test_firewall_missing_allowed_denied_key(self):
        mock_firewall_dict = {
            'items': [
                {
                }
            ]
        }
        m = self._mock_discovery
        m.build().projects().list().execute.return_value = mock_projects_dict
        m.build().firewalls().list().execute.return_value = mock_firewall_dict
        records = list(gcpcloud.GCPCloud('').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]
        self.assertEqual(len(records), 0)

    def test_firewall_rule_reference_has_firewall_link(self):
        mock_firewall_dict = {
            'items': [
                {
                    'allowed': [{}],
                    'selfLink': 'mockLink',
                }
            ]
        }
        m = self._mock_discovery
        m.build().projects().list().execute.return_value = mock_projects_dict
        m.build().firewalls().list().execute.return_value = mock_firewall_dict
        records = list(gcpcloud.GCPCloud('').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]
        self.assertEqual(records[0]['com']['reference'], 'mockLink')

    def test_firewall_rule_disabled_false_normalization(self):
        mock_firewall_dict = {
            'items': [
                {
                    'allowed': [{}],
                    'disabled': False,
                }
            ]
        }
        m = self._mock_discovery
        m.build().projects().list().execute.return_value = mock_projects_dict
        m.build().firewalls().list().execute.return_value = mock_firewall_dict
        records = list(gcpcloud.GCPCloud('').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]
        self.assertTrue(records[0]['com']['enabled'])

    def test_firewall_rule_disabled_true_normalization(self):
        mock_firewall_dict = {
            'items': [
                {
                    'allowed': [{}],
                    'disabled': True,
                }
            ]
        }
        m = self._mock_discovery
        m.build().projects().list().execute.return_value = mock_projects_dict
        m.build().firewalls().list().execute.return_value = mock_firewall_dict
        records = list(gcpcloud.GCPCloud('').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]
        self.assertFalse(records[0]['com']['enabled'])

    def test_firewall_direction_ingress_normalization(self):
        mock_firewall_dict = {
            'items': [
                {
                    'allowed': [{}],
                    'direction': 'INGRESS',
                }
            ]
        }
        m = self._mock_discovery
        m.build().projects().list().execute.return_value = mock_projects_dict
        m.build().firewalls().list().execute.return_value = mock_firewall_dict
        records = list(gcpcloud.GCPCloud('').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]
        self.assertEqual(records[0]['com']['direction'], 'in')

    def test_firewall_direction_egress_normalization(self):
        mock_firewall_dict = {
            'items': [
                {
                    'allowed': [{}],
                    'direction': 'EGRESS',
                }
            ]
        }
        m = self._mock_discovery
        m.build().projects().list().execute.return_value = mock_projects_dict
        m.build().firewalls().list().execute.return_value = mock_firewall_dict
        records = list(gcpcloud.GCPCloud('').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]
        self.assertEqual(records[0]['com']['direction'], 'out')

    def test_firewall_direction_other_normalization(self):
        mock_firewall_dict = {
            'items': [
                {
                    'allowed': [{}],
                    'direction': 'FoO',
                }
            ]
        }
        m = self._mock_discovery
        m.build().projects().list().execute.return_value = mock_projects_dict
        m.build().firewalls().list().execute.return_value = mock_firewall_dict
        records = list(gcpcloud.GCPCloud('').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]
        self.assertEqual(records[0]['com']['direction'], 'foo')

    def test_firewall_source_ranges_normalization(self):
        mock_firewall_dict = {
            'items': [
                {
                    'allowed': [{}],
                    'sourceRanges': ['40.0.0.0/8', '50.0.0.0/8'],
                }
            ]
        }
        m = self._mock_discovery
        m.build().projects().list().execute.return_value = mock_projects_dict
        m.build().firewalls().list().execute.return_value = mock_firewall_dict
        records = list(gcpcloud.GCPCloud('').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]
        self.assertEqual(records[0]['com']['source_addresses'],
                         ['40.0.0.0/8', '50.0.0.0/8'])

    def test_firewall_protocol_normalization(self):
        mock_firewall_dict = {
            'items': [
                {
                    'allowed': [{'IPProtocol': 'tcp'}],
                }
            ]
        }
        m = self._mock_discovery
        m.build().projects().list().execute.return_value = mock_projects_dict
        m.build().firewalls().list().execute.return_value = mock_firewall_dict
        records = list(gcpcloud.GCPCloud('').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]
        self.assertEqual(records[0]['com']['protocol'], 'tcp')

    def test_firewall_ports_normalization(self):
        mock_firewall_dict = {
            'items': [
                {
                    'allowed': [{'ports': ['22', '3389', '8000-8080']}],
                }
            ]
        }
        m = self._mock_discovery
        m.build().projects().list().execute.return_value = mock_projects_dict
        m.build().firewalls().list().execute.return_value = mock_firewall_dict
        records = list(gcpcloud.GCPCloud('').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]
        self.assertEqual(records[0]['com']['destination_ports'],
                         ['22', '3389', '8000-8080'])

    def test_firewall_missing_ports(self):
        mock_firewall_dict = {
            'items': [
                {
                    'allowed': [{}],
                }
            ]
        }
        m = self._mock_discovery
        m.build().projects().list().execute.return_value = mock_projects_dict
        m.build().firewalls().list().execute.return_value = mock_firewall_dict
        records = list(gcpcloud.GCPCloud('').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]
        self.assertEqual(records[0]['com']['destination_ports'], ['0-65535'])
