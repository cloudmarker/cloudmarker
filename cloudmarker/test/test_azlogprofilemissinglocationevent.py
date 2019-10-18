"""Tests for AzLogProfileMissingLocationEvent plugin."""


import copy
import unittest

from cloudmarker.events import azlogprofilemissinglocationevent

base_log_profile_id = '/subscriptions/foo_sub_id/providers/\
                    microsoft.insights/logprofiles/foo_lp_name'

base_record = {
    'com':  {
        'cloud_type':  'azure',
        'record_type': 'log_profile',
        'reference': base_log_profile_id,
    },
    'ext': {
        'reference': base_log_profile_id,
        'subscription_locations': [],
        'locations': [],
    },
    'raw': {
        'categories': [],
    }
}


class AzLogProfileMissingLocationEventTest(unittest.TestCase):
    """Tests for AzLogProfileMissingLocationEvent plugin."""

    def test_com_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['com'] = None
        plugin = azlogprofilemissinglocationevent. \
            AzLogProfileMissingLocationEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_com_bucket_cloud_type_non_azure(self):
        record = copy.deepcopy(base_record)
        record['com']['cloud_type'] = 'non_azure'
        plugin = azlogprofilemissinglocationevent. \
            AzLogProfileMissingLocationEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_com_bucket_record_type_non_log_profile(self):
        record = copy.deepcopy(base_record)
        record['com']['record_type'] = 'non_log_profile'
        plugin = azlogprofilemissinglocationevent. \
            AzLogProfileMissingLocationEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_ext_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['ext'] = None
        plugin = azlogprofilemissinglocationevent. \
            AzLogProfileMissingLocationEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_global_location_available(self):
        record = copy.deepcopy(base_record)
        record['ext']['locations'] = ['global']
        plugin = azlogprofilemissinglocationevent. \
            AzLogProfileMissingLocationEvent()
        events = list(plugin.eval(record))
        self.assertEqual(len(events), 0)

    def test_global_location_not_available(self):
        record = copy.deepcopy(base_record)
        plugin = azlogprofilemissinglocationevent. \
            AzLogProfileMissingLocationEvent()
        events = list(plugin.eval(record))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['ext']['record_type'],
                         'log_profile_missing_location_event')
        self.assertEqual(events[0]['com']['record_type'],
                         'log_profile_missing_location_event')
        self.assertEqual(events[0]['com']['cloud_type'], 'azure')
        self.assertEqual(events[0]['com']['reference'], base_log_profile_id)

    def test_all_location_not_available(self):
        record = copy.deepcopy(base_record)
        record['ext']['subscription_locations'] = \
            ['loc_1, loc_2']
        record['ext']['locations'] = ['global', 'loc_1']
        plugin = azlogprofilemissinglocationevent. \
            AzLogProfileMissingLocationEvent()
        events = list(plugin.eval(record))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['ext']['record_type'],
                         'log_profile_missing_location_event')
        self.assertEqual(events[0]['com']['record_type'],
                         'log_profile_missing_location_event')
        self.assertEqual(events[0]['com']['cloud_type'], 'azure')
        self.assertEqual(events[0]['com']['reference'], base_log_profile_id)
