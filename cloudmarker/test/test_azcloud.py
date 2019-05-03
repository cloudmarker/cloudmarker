"""Tests for AzCloud plugin."""


import unittest
from unittest import mock

from cloudmarker.clouds import azcloud


class AzCloudTest(unittest.TestCase):
    """Tests for AzCloud plugin."""

    def _patch(self, target):
        patcher = mock.patch('cloudmarker.clouds.azcloud.' + target)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def setUp(self):
        self._patch('ServicePrincipalCredentials')

        mock_record = mock.MagicMock()

        m = self._patch('SubscriptionClient')
        self._MockSubscriptionClient = m
        m().subscriptions.list.return_value = [mock_record]

        m = self._patch('ComputeManagementClient')
        self._MockComputeManagementClient = m
        m().virtual_machines.list_all.return_value = [mock_record]

        m = self._patch('NetworkManagementClient')
        self._MockNetworkManagementClient = m
        m().application_gateways.list_all.return_value = [mock_record]
        m().load_balancers.list_all.return_value = [mock_record]
        m().network_interfaces.list_all.return_value = [mock_record]
        m().network_security_groups.list_all.return_value = [mock_record]
        m().public_ip_addresses.list_all.return_value = [mock_record]

        m = self._patch('StorageManagementClient')
        self._MockStorageManagementClient = m
        m().storage_accounts.list.return_value = [mock_record]

        m = self._patch('ResourceManagementClient')
        self._ResourceManagementClient = m
        m().resource_groups.list.return_value = [mock_record]
        m().resources.list.return_value = [mock_record]

    def test_nsg_single_security_rule(self):
        mock_nsg_dict = {'security_rules': [{}]}
        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        # Note that the 'security_rules' list in the above mock NSG
        # record has only item: an empty dict. This tests the robustness
        # of AzCloud plugin when keys are missing from a security
        # rule dict. AzCloud plugin should work gracefully even if
        # all keys are missing. The only thing we care about is that for
        # every security rule dict in the raw/mock NSG record, a
        # firewall_rule record is generated. This pattern is used in
        # other tests too in this test module.

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertEqual(len(records), 1)

    def test_nsg_multiple_security_rules(self):
        mock_nsg_dict = {'security_rules': [{}, {}]}
        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertEqual(len(records), 2)

    def test_nsg_zero_security_rules(self):
        mock_nsg_dict = {'security_rules': []}
        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertEqual(len(records), 0)

    def test_nsg_missing_security_rules(self):
        mock_nsg_dict = {}
        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertEqual(len(records), 0)

    def test_firewall_rule_reference_has_security_rule_id(self):
        mock_nsg_dict = {'security_rules': [{'id': 'mock_id'}]}
        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertEqual(records[0]['com']['reference'], 'mock_id')

    def test_firewall_rule_provisioning_state_succeeded_normalization(self):
        mock_nsg_dict = {
            'security_rules': [{'provisioning_state': 'Succeeded'}]
        }
        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertTrue(records[0]['com']['enabled'])

    def test_firewall_rule_provisioning_state_other_normalization(self):
        mock_nsg_dict = {
            'security_rules': [{'provisioning_state': 'Failed'}]
        }
        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertFalse(records[0]['com']['enabled'])

    def test_nsg_direction_inbound_normalization(self):
        mock_nsg_dict = {'security_rules': [{'direction': 'Inbound'}]}
        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertEqual(records[0]['com']['direction'], 'in')

    def test_nsg_direction_outbound_normalization(self):
        mock_nsg_dict = {'security_rules': [{'direction': 'Outbound'}]}
        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertEqual(records[0]['com']['direction'], 'out')

    def test_nsg_direction_other_normalization(self):
        mock_nsg_dict = {'security_rules': [{'direction': 'FoO'}]}
        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertEqual(records[0]['com']['direction'], 'foo')

    def test_nsg_access_allow_normalization(self):
        mock_nsg_dict = {'security_rules': [{'access': 'Allow'}]}
        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertEqual(records[0]['com']['access'], 'allow')

    def test_nsg_access_deny_normalization(self):
        mock_nsg_dict = {'security_rules': [{'access': 'Deny'}]}
        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertEqual(records[0]['com']['access'], 'deny')

    def test_nsg_access_other_normalization(self):
        mock_nsg_dict = {'security_rules': [{'access': 'FoO'}]}
        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertEqual(records[0]['com']['access'], 'foo')

    def test_nsg_source_address_prefix_asterisk_normalization(self):
        mock_nsg_dict = {'security_rules': [{'source_address_prefix': '*'}]}
        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertEqual(records[0]['com']['source_addresses'], ['0.0.0.0/0'])

    def test_nsg_source_address_prefix_internet_normalization(self):
        mock_nsg_dict = {
            'security_rules': [{'source_address_prefix': 'Internet'}]
        }
        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertEqual(records[0]['com']['source_addresses'], ['0.0.0.0/0'])

    def test_nsg_source_address_prefix_cidr_normalization(self):
        mock_nsg_dict = {
            'security_rules': [{'source_address_prefix': '40.0.0.0/8'}]
        }
        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertEqual(records[0]['com']['source_addresses'], ['40.0.0.0/8'])

    def test_nsg_source_address_prefixes_normalization(self):
        mock_nsg_dict = {
            'security_rules': [{'source_address_prefixes': ['40.0.0.0/8']}]
        }
        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertEqual(records[0]['com']['source_addresses'], ['40.0.0.0/8'])

    def test_nsg_source_address_prefix_and_prefixes_both_present(self):
        mock_nsg_dict = {
            'security_rules': [
                {
                    'source_address_prefix': '40.0.0.0/8',
                    'source_address_prefixes': ['41.0.0.0/8', '42.0.0.0/8'],
                }
            ]
        }

        # We do not expect both 'source_address_prefix' and
        # 'source_address_prefixes' to be present in the same security
        # rule but we are making sure here that even if they were to be
        # present, we are able to handle it in a sensible manner.

        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertEqual(records[0]['com']['source_addresses'],
                         ['40.0.0.0/8', '41.0.0.0/8', '42.0.0.0/8'])

    def test_nsg_protocol_name_normalization(self):
        mock_nsg_dict = {'security_rules': [{'protocol': 'TCP'}]}
        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertEqual(records[0]['com']['protocol'], 'tcp')

    def test_nsg_protocol_asterisk_normalization(self):
        mock_nsg_dict = {'security_rules': [{'protocol': '*'}]}
        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertEqual(records[0]['com']['protocol'], 'all')

    def test_nsg_destination_port_range_asterisk_normalization(self):
        mock_nsg_dict = {'security_rules': [{'destination_port_range': '*'}]}
        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertEqual(records[0]['com']['destination_ports'], ['0-65535'])

    def test_nsg_destination_port_range_number_normalization(self):
        mock_nsg_dict = {'security_rules': [{'destination_port_range': '22'}]}
        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertEqual(records[0]['com']['destination_ports'], ['22'])

    def test_nsg_destination_port_range_range_normalization(self):
        mock_nsg_dict = {
            'security_rules': [{'destination_port_range': '8000-8080'}]
        }
        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertEqual(records[0]['com']['destination_ports'], ['8000-8080'])

    def test_nsg_destination_port_ranges_normalization(self):
        mock_nsg_dict = {
            'security_rules': [
                {'destination_port_ranges': ['22', '8000-8080']}
            ]
        }
        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertEqual(records[0]['com']['destination_ports'],
                         ['22', '8000-8080'])

    def test_nsg_destination_port_range_and_ranges_both_present(self):
        mock_nsg_dict = {
            'security_rules': [
                {
                    'destination_port_range': '22',
                    'destination_port_ranges': ['3389', '8000-8080'],
                }
            ]
        }

        # We do not expect both 'destination_port_range' and
        # 'destination_port_ranges' to be present in the same security
        # rule but we are making sure here that even if they were to be
        # present, we are able to handle it in a sensible manner.

        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertEqual(records[0]['com']['destination_ports'],
                         ['22', '3389', '8000-8080'])

    def test_nsg_destination_port_range_empty(self):
        mock_nsg_dict = {
            'security_rules': [
                {
                    'destination_port_range': '',
                }
            ]
        }

        # We do not expect both 'destination_port_range' and
        # 'destination_port_ranges' to be present in the same security
        # rule but we are making sure here that even if they were to be
        # present, we are able to handle it in a sensible manner.

        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertEqual(records[0]['com']['destination_ports'], [])

    def test_nsg_destination_port_range_empty_and_port_ranges(self):
        mock_nsg_dict = {
            'security_rules': [
                {
                    'destination_port_range': '',
                    'destination_port_ranges': ['3389', '8000-8080'],
                }
            ]
        }

        # We do not expect both 'destination_port_range' and
        # 'destination_port_ranges' to be present in the same security
        # rule but we are making sure here that even if they were to be
        # present, we are able to handle it in a sensible manner.

        mock_nsg = mock.Mock()
        mock_nsg.as_dict.return_value = mock_nsg_dict

        m = self._MockNetworkManagementClient
        m().network_security_groups.list_all.return_value = [mock_nsg]

        records = list(azcloud.AzCloud('', '', '').read())
        records = [
            r for r in records
            if r['com']['record_type'] == 'firewall_rule'
        ]

        self.assertEqual(records[0]['com']['destination_ports'],
                         ['3389', '8000-8080'])
