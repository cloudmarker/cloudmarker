"""Tests for AzLogProfileMissingCategoryEvent plugin."""


import copy
import unittest

from cloudmarker.events import azlogprofilemissingcategoryevent

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
    },
    'raw': {
        'categories': [],
    }
}


class AzLogProfileMissingCategoryEventTest(unittest.TestCase):
    """Tests for AzLogProfileMissingCategoryEvent plugin."""

    def test_com_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['com'] = None
        plugin = azlogprofilemissingcategoryevent. \
            AzLogProfileMissingCategoryEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_com_bucket_cloud_type_non_azure(self):
        record = copy.deepcopy(base_record)
        record['com']['cloud_type'] = 'non_azure'
        plugin = azlogprofilemissingcategoryevent. \
            AzLogProfileMissingCategoryEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_com_bucket_record_type_non_log_profile(self):
        record = copy.deepcopy(base_record)
        record['com']['record_type'] = 'non_log_profile'
        plugin = azlogprofilemissingcategoryevent. \
            AzLogProfileMissingCategoryEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_ext_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['ext'] = None
        plugin = azlogprofilemissingcategoryevent. \
            AzLogProfileMissingCategoryEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_raw_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['raw'] = None
        plugin = azlogprofilemissingcategoryevent. \
            AzLogProfileMissingCategoryEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_all_event_types_missing(self):
        record = copy.deepcopy(base_record)
        plugin = azlogprofilemissingcategoryevent. \
            AzLogProfileMissingCategoryEvent()
        events = list(plugin.eval(record))
        self.assertEqual(len(events), 1)

    def test_single_event_types_missing(self):
        record = copy.deepcopy(base_record)
        record['raw']['categories'] = ['Write', 'Delete']
        plugin = azlogprofilemissingcategoryevent. \
            AzLogProfileMissingCategoryEvent()
        events = list(plugin.eval(record))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['ext']['record_type'],
                         'log_profile_missing_category_event')
        self.assertEqual(events[0]['com']['record_type'],
                         'log_profile_missing_category_event')
        self.assertEqual(events[0]['com']['cloud_type'], 'azure')
        self.assertEqual(events[0]['com']['reference'], base_log_profile_id)
