"""Tests for AzPostgresLogDurationEvent plugin."""


import copy
import unittest

from cloudmarker.events import azpostgreslogdurationevent

base_record = {
    'com':  {
        'cloud_type': 'azure',
        'record_type': 'rdbms',
    },
    'ext': {
        'record_type': 'postgresql_server',
        'log_duration_enabled': False
    }
}


class AzPostgresLogCheckpointsEventTest(unittest.TestCase):
    """Tests for AzPostgresLogDurationEvent plugin."""

    def test_com_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['com'] = None
        plugin = azpostgreslogdurationevent.AzPostgresLogDurationEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_cloud_non_azure(self):
        record = copy.deepcopy(base_record)
        record['com']['cloud_type'] = 'non_azure'
        plugin = azpostgreslogdurationevent.AzPostgresLogDurationEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_record_type_non_rdbms(self):
        record = copy.deepcopy(base_record)
        record['com']['record_type'] = 'non_rdbms'
        plugin = azpostgreslogdurationevent.AzPostgresLogDurationEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_ext_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['ext'] = None
        plugin = azpostgreslogdurationevent.AzPostgresLogDurationEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_record_type_non_postgresql_server(self):
        record = copy.deepcopy(base_record)
        record['ext']['record_type'] = 'non_postgresql_server'
        plugin = azpostgreslogdurationevent.AzPostgresLogDurationEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_log_duration_enabled(self):
        record = copy.deepcopy(base_record)
        record['ext']['log_duration_enabled'] = True
        plugin = azpostgreslogdurationevent.AzPostgresLogDurationEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_log_duration_disabled(self):
        record = copy.deepcopy(base_record)
        plugin = azpostgreslogdurationevent.AzPostgresLogDurationEvent()
        events = list(plugin.eval(record))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['ext']['record_type'],
                         'postgres_log_duration_event')
        self.assertEqual(events[0]['com']['cloud_type'],
                         'azure')
        self.assertEqual(events[0]['com']['record_type'],
                         'postgres_log_duration_event')
        self.assertTrue('reference' in events[0]['com'])
        self.assertIsNotNone(events[0]['com']['description'])
        self.assertIsNotNone(events[0]['com']['recommendation'])
