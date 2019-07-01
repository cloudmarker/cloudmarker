"""Tests for AzSQLDatabaseTDEEvent plugin."""


import copy
import unittest

from cloudmarker.events import azsqldatabasetdeevent

base_record = {
    'com':  {
        'cloud_type': 'azure'
    },
    'ext': {
        'record_type': 'sql_db',
        'tde_enabled': True
    }
}


class AzSQLDatabaseDisabledTDEEventTest(unittest.TestCase):
    """Tests for AzSQLDatabaseTDEEvent plugin."""

    def test_com_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['com'] = None
        plugin = azsqldatabasetdeevent.AzSQLDatabaseTDEEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_cloud_non_azure(self):
        record = copy.deepcopy(base_record)
        record['com']['cloud_type'] = 'non_azure'
        plugin = azsqldatabasetdeevent.AzSQLDatabaseTDEEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_ext_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['ext'] = None
        plugin = azsqldatabasetdeevent.AzSQLDatabaseTDEEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_record_type_non_sql_db(self):
        record = copy.deepcopy(base_record)
        record['ext']['record_type'] = 'non_sql_db'
        plugin = azsqldatabasetdeevent.AzSQLDatabaseTDEEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_tde_enabled(self):
        record = copy.deepcopy(base_record)
        plugin = azsqldatabasetdeevent.AzSQLDatabaseTDEEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_tde_disabled(self):
        record = copy.deepcopy(base_record)
        record['ext']['tde_enabled'] = False
        plugin = azsqldatabasetdeevent.AzSQLDatabaseTDEEvent()
        events = list(plugin.eval(record))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['ext']['record_type'],
                         'sql_db_tde_event')
        self.assertEqual(events[0]['com']['cloud_type'],
                         'azure')
        self.assertEqual(events[0]['com']['record_type'],
                         'sql_db_tde_event')
        self.assertTrue('reference' in events[0]['com'])
        self.assertIsNotNone(events[0]['com']['description'])
        self.assertIsNotNone(events[0]['com']['recommendation'])
