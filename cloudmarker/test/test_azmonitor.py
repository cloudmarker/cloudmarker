"""Tests for AzMonitor plugin."""

import copy
import unittest
from unittest import mock

from cloudmarker.clouds import azmonitor

base_sub_id = 'foo_sub_id'

base_sub_display_name = 'foo_display_name'

base_sub_state = 'foo_state'

base_subscription_record = {
    'subscription_id': base_sub_id,
    'display_name': base_sub_display_name,
    'state': base_sub_state
}

base_log_profile_id = '/subscriptions/foo_sub_id/providers/\
                    microsoft.insights/logprofiles/foo_lp_name'

base_log_profile = {
    'id': base_log_profile_id
}


class SimpleMock:
    """A simple picklable class.

    AzSQL sends subscription object and cloud records from main
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
    """Tests for AzMonitor plugin."""

    def _patch(self, target):
        patcher = mock.patch('cloudmarker.clouds.azmonitor.' + target)
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
        m = self._patch('MonitorManagementClient')
        self._MockMonitorManagementClient = m
        m().log_profiles.list.return_value = [mock_record]

    def test_log_profile(self):
        mock_log_profile_dict = copy.deepcopy(base_log_profile)
        mock_log_profile = SimpleMock(mock_log_profile_dict)
        m = self._MockMonitorManagementClient
        m().log_profiles.list.return_value = [mock_log_profile]
        records = list(azmonitor.AzMonitor('', '', '').read())
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['ext']['cloud_type'], 'azure')
        self.assertEqual(records[0]['ext']['record_type'], 'log_profile')
        self.assertEqual(records[0]['ext']['subscription_id'], base_sub_id)
        self.assertEqual(records[0]['ext']['subscription_name'],
                         base_sub_display_name)
        self.assertEqual(records[0]['ext']['subscription_state'],
                         base_sub_state)
        self.assertEqual(records[0]['com']['cloud_type'], 'azure')
        self.assertEqual(records[0]['com']['record_type'], 'log_profile')
        self.assertEqual(records[0]['com']['reference'], base_log_profile_id)
