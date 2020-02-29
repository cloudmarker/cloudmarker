"""Tests for AzWebAppHttp20Event plugin."""


import copy
import unittest

from cloudmarker.events import azwebapphttp20event

base_record = {
    'ext':  {
        'record_type': 'web_app_config',
        'cloud_type':  'azure',
        'http20_enabled': True
    },
    'com':  {
        'cloud_type':  'azure'
    }
}


class AzWebAppHttp20EventTest(unittest.TestCase):
    """Tests for AzWebAppHttp20Event plugin."""

    def test_com_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['com'] = None
        plugin = azwebapphttp20event.AzWebAppHttp20Event()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_cloud_type_non_azure(self):
        record = copy.deepcopy(base_record)
        record['com']['cloud_type'] = 'non_azure'
        plugin = azwebapphttp20event.AzWebAppHttp20Event()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_ext_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['ext'] = None
        plugin = azwebapphttp20event.AzWebAppHttp20Event()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_record_type_non_web_app_config(self):
        record = copy.deepcopy(base_record)
        record['ext']['record_type'] = 'non_web_app_config'
        plugin = azwebapphttp20event.AzWebAppHttp20Event()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_http20_enabled(self):
        record = copy.deepcopy(base_record)
        record['ext']['http20_enabled'] = True
        plugin = azwebapphttp20event.AzWebAppHttp20Event()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_http20_disabled(self):
        record = copy.deepcopy(base_record)
        record['ext']['http20_enabled'] = False
        plugin = azwebapphttp20event.AzWebAppHttp20Event()
        events = list(plugin.eval(record))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['ext']['record_type'],
                         'web_app_http20_event')
        self.assertEqual(events[0]['com']['record_type'],
                         'web_app_http20_event')
