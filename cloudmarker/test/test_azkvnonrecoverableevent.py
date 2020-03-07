"""Tests for AzKVNonRecoverableEvent plugin."""


import copy
import unittest

from cloudmarker.events import azkvnonrecoverableevent

base_record = {
    'com':  {
        'cloud_type':  'azure',
        'record_type': 'key_vault'
    },
    'ext': {
        'record_type': 'key_vault',
        'recoverable': False,
    }
}


class AzKVNonRecoverableEventTest(unittest.TestCase):
    """Tests for AzKVNonRecoverableEvent plugin."""

    def test_com_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['com'] = None
        plugin = azkvnonrecoverableevent. \
            AzKVNonRecoverableEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_com_bucket_cloud_type_non_azure(self):
        record = copy.deepcopy(base_record)
        record['com']['cloud_type'] = 'non_azure'
        plugin = azkvnonrecoverableevent. \
            AzKVNonRecoverableEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_ext_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['ext'] = None
        plugin = azkvnonrecoverableevent. \
            AzKVNonRecoverableEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_ext_bucket_record_type_non_key_vault(self):
        record = copy.deepcopy(base_record)
        record['ext']['record_type'] = 'non_key_vault'
        plugin = azkvnonrecoverableevent. \
            AzKVNonRecoverableEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_key_vault_recoverable(self):
        record = copy.deepcopy(base_record)
        record['ext']['recoverable'] = True
        plugin = azkvnonrecoverableevent. \
            AzKVNonRecoverableEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_key_vault_non_recoverable(self):
        record = copy.deepcopy(base_record)
        plugin = azkvnonrecoverableevent. \
            AzKVNonRecoverableEvent()
        events = list(plugin.eval(record))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['ext']['record_type'],
                         'key_vault_non_recoverable_event')
        self.assertEqual(events[0]['com']['record_type'],
                         'key_vault_non_recoverable_event')
