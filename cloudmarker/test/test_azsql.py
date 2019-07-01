"""Tests for AzSQL plugin."""

import copy
import unittest
from unittest import mock

from cloudmarker.clouds import azsql

base_sql_server = {
    'name': 'foo_sql_server_name',
    'id': '/subscriptions/foo_sub_id/resourceGroups/\
           foo_rg/providers/Microsoft.Sql/servers/foo_server'
}

base_sql_db_id = 'foo_db_id'
base_sql_db = {
    'name': 'foo_sql_db',
    'id': base_sql_db_id
}

base_sql_tde = {
    'status': 'Enabled'
}

base_sub_id = 'foo_sub_id'

base_sub_display_name = 'foo_display_name'

base_sub_state = 'foo_state'

base_subscription_record = {
    'subscription_id': base_sub_id,
    'display_name': base_sub_display_name,
    'state': base_sub_state
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
    """Tests for AzSQL plugin."""

    def _patch(self, target):
        patcher = mock.patch('cloudmarker.clouds.azsql.' + target)
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
        m = self._patch('SqlManagementClient')
        self._MockSqlManagementClient = m
        m().servers.list.return_value = [mock_record]
        m().databases.list_by_server.return_value = [mock_record]
        m().transparent_data_encryptions.get.return_value = [mock_record]

    def test_sql_single_db_tde_enabled(self):
        mock_sql_server_dict = copy.deepcopy(base_sql_server)
        mock_sql_server = SimpleMock(mock_sql_server_dict)
        mock_sql_db_dict = copy.deepcopy(base_sql_db)
        mock_sql_db = SimpleMock(mock_sql_db_dict)
        mock_sql_db_tde_dict = copy.deepcopy(base_sql_tde)
        mock_sql_db_tde = SimpleMock(mock_sql_db_tde_dict)
        m = self._MockSqlManagementClient
        m().servers.list.return_value = [mock_sql_server]
        m().databases.list_by_server.return_value = [mock_sql_db]
        m().transparent_data_encryptions.get.return_value = mock_sql_db_tde
        records = list(azsql.AzSQL('', '', '').read())
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['ext']['cloud_type'], 'azure')
        self.assertEqual(records[0]['ext']['record_type'], 'sql_db')
        self.assertEqual(records[0]['ext']['subscription_id'], base_sub_id)
        self.assertEqual(records[0]['ext']['subscription_name'],
                         base_sub_display_name)
        self.assertEqual(records[0]['ext']['subscription_state'],
                         base_sub_state)
        self.assertEqual(records[0]['ext']['tde_enabled'], True)
        self.assertEqual(records[0]['com']['cloud_type'], 'azure')
        self.assertEqual(records[0]['com']['record_type'], 'database')
        self.assertEqual(records[0]['com']['reference'], base_sql_db_id)

    def test_sql_single_db_tde_disabled(self):
        mock_sql_server_dict = copy.deepcopy(base_sql_server)
        mock_sql_server = SimpleMock(mock_sql_server_dict)
        mock_sql_db_dict = copy.deepcopy(base_sql_db)
        mock_sql_db = SimpleMock(mock_sql_db_dict)
        mock_sql_db_tde_dict = copy.deepcopy(base_sql_tde)
        mock_sql_db_tde_dict['status'] = 'Disabled'
        mock_sql_db_tde = SimpleMock(mock_sql_db_tde_dict)
        m = self._MockSqlManagementClient
        m().servers.list.return_value = [mock_sql_server]
        m().databases.list_by_server.return_value = [mock_sql_db]
        m().transparent_data_encryptions.get.return_value = mock_sql_db_tde
        records = list(azsql.AzSQL('', '', '').read())
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['ext']['cloud_type'], 'azure')
        self.assertEqual(records[0]['ext']['record_type'], 'sql_db')
        self.assertEqual(records[0]['ext']['subscription_id'], base_sub_id)
        self.assertEqual(records[0]['ext']['subscription_name'],
                         base_sub_display_name)
        self.assertEqual(records[0]['ext']['subscription_state'],
                         base_sub_state)
        self.assertEqual(records[0]['ext']['tde_enabled'], False)
        self.assertEqual(records[0]['com']['cloud_type'], 'azure')
        self.assertEqual(records[0]['com']['record_type'], 'database')
        self.assertEqual(records[0]['com']['reference'], base_sql_db_id)
