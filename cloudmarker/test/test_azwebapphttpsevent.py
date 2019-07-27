"""Tests for AzWebAppHttpsEvent plugin."""


import copy
import unittest

from cloudmarker.events import azwebapphttpsevent

base_record = {
    'ext':  {
        'record_type': 'web_app_config',
        'cloud_type':  'azure',
        'https_only': True
    },
    'com':  {
        'cloud_type':  'azure'
    }
}


class AzWebAppHttpsEventTest(unittest.TestCase):
    """Tests for AzWebAppHttpsEvent plugin."""

    def test_com_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['com'] = None
        plugin = azwebapphttpsevent.AzWebAppHttpsEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_cloud_type_non_azure(self):
        record = copy.deepcopy(base_record)
        record['com']['cloud_type'] = 'non_azure'
        plugin = azwebapphttpsevent.AzWebAppHttpsEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_ext_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['ext'] = None
        plugin = azwebapphttpsevent.AzWebAppHttpsEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_record_type_non_web_app_config(self):
        record = copy.deepcopy(base_record)
        record['ext']['record_type'] = 'non_web_app_config'
        plugin = azwebapphttpsevent.AzWebAppHttpsEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_https_only(self):
        record = copy.deepcopy(base_record)
        record['ext']['https_only'] = True
        plugin = azwebapphttpsevent.AzWebAppHttpsEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_not_https_only(self):
        record = copy.deepcopy(base_record)
        record['ext']['https_only'] = False
        plugin = azwebapphttpsevent.AzWebAppHttpsEvent()
        events = list(plugin.eval(record))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['ext']['record_type'],
                         'web_app_https_event')
        self.assertEqual(events[0]['com']['record_type'],
                         'web_app_https_event')
