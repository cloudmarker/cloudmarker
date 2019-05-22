"""Tests for RDBMSEnforceTLSEvent plugin."""


import copy
import unittest

from cloudmarker.events import rdbmsenforcetlsevent

base_record = {
    'com':  {
        'tls_enforced':  True,
        'record_type': 'rdbms',
    }
}


class RDBMSEnforceTLSEventTest(unittest.TestCase):
    """Tests for RDBMSEnforceTLSEvent plugin."""

    def test_com_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['com'] = None
        plugin = rdbmsenforcetlsevent.RDBMSEnforceTLSEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_com_bucket_record_type_non_rdbms(self):
        record = copy.deepcopy(base_record)
        record['com']['record_type'] = 'non_rdbms'
        plugin = rdbmsenforcetlsevent.RDBMSEnforceTLSEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_tls_enforcement_enabled(self):
        record = copy.deepcopy(base_record)
        plugin = rdbmsenforcetlsevent.RDBMSEnforceTLSEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_tls_enforcement_missing(self):
        record = copy.deepcopy(base_record)
        del record['com']['tls_enforced']
        plugin = rdbmsenforcetlsevent.RDBMSEnforceTLSEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_tls_enforcement_none(self):
        record = copy.deepcopy(base_record)
        record['com']['tls_enforced'] = None
        plugin = rdbmsenforcetlsevent.RDBMSEnforceTLSEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_tls_enforcement_disbled(self):
        record = copy.deepcopy(base_record)
        record['com']['tls_enforced'] = False
        plugin = rdbmsenforcetlsevent.RDBMSEnforceTLSEvent()
        events = list(plugin.eval(record))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['ext']['record_type'],
                         'rdbms_enforce_tls_event')
        self.assertEqual(events[0]['com']['record_type'],
                         'rdbms_enforce_tls_event')
