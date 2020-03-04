"""Tests for AzStorageAccountAllowTrustedServicesEvent plugin."""


import copy
import unittest

from cloudmarker.events import azstorageaccountallowtrustedservicesevent

base_record = {
    'com':  {
        'cloud_type': 'azure',
        'record_type': 'storage_account_properties',
    },
    'ext': {
        'record_type': 'storage_account_properties',
        'trusted_services_allowed': False
    }
}


class AzStorageAccountAllowTrustedServicesEventTest(unittest.TestCase):
    """Tests for AzStorageAccountAllowTrustedServicesEvent plugin."""

    def test_com_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['com'] = None
        plugin = azstorageaccountallowtrustedservicesevent. \
            AzStorageAccountAllowTrustedServicesEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_cloud_non_azure(self):
        record = copy.deepcopy(base_record)
        record['com']['cloud_type'] = 'non_azure'
        plugin = azstorageaccountallowtrustedservicesevent. \
            AzStorageAccountAllowTrustedServicesEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_record_type_non_storage_account_properties(self):
        record = copy.deepcopy(base_record)
        record['ext']['record_type'] = 'non_storage_account_properties'
        plugin = azstorageaccountallowtrustedservicesevent. \
            AzStorageAccountAllowTrustedServicesEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_ext_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['ext'] = None
        plugin = azstorageaccountallowtrustedservicesevent. \
            AzStorageAccountAllowTrustedServicesEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_trusted_services_allowed(self):
        record = copy.deepcopy(base_record)
        record['ext']['trusted_services_allowed'] = True
        plugin = azstorageaccountallowtrustedservicesevent. \
            AzStorageAccountAllowTrustedServicesEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_trusted_services_not_allowed(self):
        record = copy.deepcopy(base_record)
        plugin = azstorageaccountallowtrustedservicesevent. \
            AzStorageAccountAllowTrustedServicesEvent()
        events = list(plugin.eval(record))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['ext']['record_type'],
                         'storage_account_allow_trusted_services_event')
        self.assertEqual(events[0]['com']['cloud_type'],
                         'azure')
        self.assertEqual(events[0]['com']['record_type'],
                         'storage_account_allow_trusted_services_event')
        self.assertTrue('reference' in events[0]['com'])
        self.assertIsNotNone(events[0]['com']['description'])
        self.assertIsNotNone(events[0]['com']['recommendation'])
