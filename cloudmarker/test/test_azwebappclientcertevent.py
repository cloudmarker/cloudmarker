"""Tests for AzWebAppClientCertEvent plugin."""


import copy
import unittest

from cloudmarker.events import azwebappclientcertevent

base_record = {
    'ext':  {
        'record_type': 'web_app_config',
        'cloud_type':  'azure',
        'client_cert_enabled': True
    },
    'com':  {
        'cloud_type':  'azure'
    }
}


class AzWebAppClientCertEventTest(unittest.TestCase):
    """Tests for AzWebAppClientCertEvent plugin."""

    def test_com_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['com'] = None
        plugin = azwebappclientcertevent.AzWebAppClientCertEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_cloud_type_non_azure(self):
        record = copy.deepcopy(base_record)
        record['com']['cloud_type'] = 'non_azure'
        plugin = azwebappclientcertevent.AzWebAppClientCertEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_ext_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['ext'] = None
        plugin = azwebappclientcertevent.AzWebAppClientCertEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_record_type_non_web_app_config(self):
        record = copy.deepcopy(base_record)
        record['ext']['record_type'] = 'non_web_app_config'
        plugin = azwebappclientcertevent.AzWebAppClientCertEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_client_cert_enabled(self):
        record = copy.deepcopy(base_record)
        record['ext']['client_cert_enabled'] = True
        plugin = azwebappclientcertevent.AzWebAppClientCertEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_client_cert_disabled(self):
        record = copy.deepcopy(base_record)
        record['ext']['client_cert_enabled'] = False
        plugin = azwebappclientcertevent.AzWebAppClientCertEvent()
        events = list(plugin.eval(record))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['ext']['record_type'],
                         'web_app_client_certificate_event')
        self.assertEqual(events[0]['com']['record_type'],
                         'web_app_client_certificate_event')
