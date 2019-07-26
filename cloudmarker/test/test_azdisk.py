"""Tests for AzDisk plugin."""

import copy
import unittest
from unittest import mock

from cloudmarker.clouds import azdisk

base_sub_id = 'foo_sub_id'

base_sub_display_name = 'foo_display_name'

base_sub_state = 'foo_state'

base_subscription_record = {
    'subscription_id': base_sub_id,
    'display_name': base_sub_display_name,
    'state': base_sub_state
}

base_disk_id = '/subscriptions/foo_sub_id/resourceGroups/foo_rg_name/ \
                providers/Microsoft.Compute/disks/foo_disk_name'

base_disk = {
    'id': base_disk_id
}


class SimpleMock:
    """A simple picklable class.

    AzDisk sends subscription object and cloud records from main
    process to worker processes and vice versa, so any mocks we use need
    to be picklable (serializable). The :class:`unittest.mock.Mock` and
    :class:`unittest.mock.MagicMock` classes are unpicklable, therefore
    we create our own mock class here.
    """

    def __init__(self, data=None):
        self._data = data if data else {}

    def as_dict(self):
        return self._data


class AzSQLTest(unittest.TestCase):
    """Tests for AzDisk plugin."""

    def _patch(self, target):
        patcher = mock.patch('cloudmarker.clouds.azdisk.' + target)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def setUp(self):
        self._patch('ServicePrincipalCredentials')
        mock_sub_record_dict = copy.deepcopy(base_subscription_record)
        mock_sub_record = SimpleMock(mock_sub_record_dict)
        m = self._patch('SubscriptionClient')
        self._MockSubscriptionClient = m
        m().subscriptions.list.return_value = [mock_sub_record]
        mock_record = SimpleMock()
        m = self._patch('ComputeManagementClient')
        self._MockComputeManagementClient = m
        m().disks.get.return_value = [mock_record]

    def test_attached_disk(self):
        mock_disk_dict = copy.deepcopy(base_disk)
        mock_disk_dict['managed_by'] = 'foo_vm'
        mock_disk = SimpleMock(mock_disk_dict)
        m = self._MockComputeManagementClient
        m().disks.list.return_value = [mock_disk]
        m().disks.get.return_value = mock_disk
        records = list(azdisk.AzDisk('', '', '').read())
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['ext']['cloud_type'], 'azure')
        self.assertEqual(records[0]['ext']['record_type'], 'disk')
        self.assertEqual(records[0]['ext']['disk_type'], 'attached')
        self.assertEqual(records[0]['ext']['subscription_id'], base_sub_id)
        self.assertEqual(records[0]['ext']['subscription_name'],
                         base_sub_display_name)
        self.assertEqual(records[0]['ext']['subscription_state'],
                         base_sub_state)
        self.assertEqual(records[0]['com']['cloud_type'], 'azure')
        self.assertEqual(records[0]['com']['record_type'], 'disk')
        self.assertEqual(records[0]['com']['reference'], base_disk_id)

    def test_managed_by_missing(self):
        mock_disk_dict = copy.deepcopy(base_disk)
        mock_disk = SimpleMock(mock_disk_dict)
        m = self._MockComputeManagementClient
        m().disks.list.return_value = [mock_disk]
        m().disks.get.return_value = mock_disk
        records = list(azdisk.AzDisk('', '', '').read())
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['ext']['cloud_type'], 'azure')
        self.assertEqual(records[0]['ext']['record_type'], 'disk')
        self.assertEqual(records[0]['ext']['disk_type'], 'unattached')
        self.assertEqual(records[0]['ext']['subscription_id'], base_sub_id)
        self.assertEqual(records[0]['ext']['subscription_name'],
                         base_sub_display_name)
        self.assertEqual(records[0]['ext']['subscription_state'],
                         base_sub_state)
        self.assertEqual(records[0]['com']['cloud_type'], 'azure')
        self.assertEqual(records[0]['com']['record_type'], 'disk')
        self.assertEqual(records[0]['com']['reference'], base_disk_id)

    def test_managed_by_blank(self):
        mock_disk_dict = copy.deepcopy(base_disk)
        mock_disk_dict['managed_by'] = ''
        mock_disk = SimpleMock(mock_disk_dict)
        m = self._MockComputeManagementClient
        m().disks.list.return_value = [mock_disk]
        m().disks.get.return_value = mock_disk
        records = list(azdisk.AzDisk('', '', '').read())
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['ext']['cloud_type'], 'azure')
        self.assertEqual(records[0]['ext']['record_type'], 'disk')
        self.assertEqual(records[0]['ext']['disk_type'], 'unattached')
        self.assertEqual(records[0]['ext']['subscription_id'], base_sub_id)
        self.assertEqual(records[0]['ext']['subscription_name'],
                         base_sub_display_name)
        self.assertEqual(records[0]['ext']['subscription_state'],
                         base_sub_state)
        self.assertEqual(records[0]['com']['cloud_type'], 'azure')
        self.assertEqual(records[0]['com']['record_type'], 'disk')
        self.assertEqual(records[0]['com']['reference'], base_disk_id)
