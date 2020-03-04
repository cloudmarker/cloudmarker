"""Tests for AzStorageAccountDefaultNetworkAccessEvent plugin."""


import copy
import unittest

from cloudmarker.events import azstorageaccountdefaultnetworkaccessevent

base_record = {
    'com':  {
        'cloud_type': 'azure',
        'record_type': 'storage_account_properties',
    },
    'ext': {
        'record_type': 'storage_account_properties',
        'default_network_access_allowed': True
    }
}


class AzStorageAccountDefaultNetworkAccessEventTest(unittest.TestCase):
    """Tests for AzStorageAccountDefaultNetworkAccessEvent plugin."""

    def test_com_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['com'] = None
        plugin = azstorageaccountdefaultnetworkaccessevent. \
            AzStorageAccountDefaultNetworkAccessEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_cloud_non_azure(self):
        record = copy.deepcopy(base_record)
        record['com']['cloud_type'] = 'non_azure'
        plugin = azstorageaccountdefaultnetworkaccessevent. \
            AzStorageAccountDefaultNetworkAccessEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_record_type_non_storage_account_properties(self):
        record = copy.deepcopy(base_record)
        record['ext']['record_type'] = 'non_storage_account_properties'
        plugin = azstorageaccountdefaultnetworkaccessevent. \
            AzStorageAccountDefaultNetworkAccessEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_ext_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['ext'] = None
        plugin = azstorageaccountdefaultnetworkaccessevent. \
            AzStorageAccountDefaultNetworkAccessEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_default_network_access_not_allowed(self):
        record = copy.deepcopy(base_record)
        record['ext']['default_network_access_allowed'] = False
        plugin = azstorageaccountdefaultnetworkaccessevent. \
            AzStorageAccountDefaultNetworkAccessEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_default_network_access_allowed(self):
        record = copy.deepcopy(base_record)
        plugin = azstorageaccountdefaultnetworkaccessevent. \
            AzStorageAccountDefaultNetworkAccessEvent()
        events = list(plugin.eval(record))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['ext']['record_type'],
                         'storage_account_default_network_access_event')
        self.assertEqual(events[0]['com']['cloud_type'],
                         'azure')
        self.assertEqual(events[0]['com']['record_type'],
                         'storage_account_default_network_access_event')
        self.assertTrue('reference' in events[0]['com'])
        self.assertIsNotNone(events[0]['com']['description'])
        self.assertIsNotNone(events[0]['com']['recommendation'])
