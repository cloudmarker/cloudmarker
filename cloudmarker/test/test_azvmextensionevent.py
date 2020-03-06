"""Tests for AzVMExtensionEvent plugin."""


import copy
import unittest

from cloudmarker.events import azvmextensionevent

base_record = {
    'ext':  {
        'record_type': 'vm_instance_view',
        'extensions':  []
    },
    'com':  {
        'cloud_type':  'azure'
    }
}


class AzVMExtensionEventTest(unittest.TestCase):
    """Tests for AzVMExtensionEvent plugin."""

    def test_com_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['com'] = None
        plugin = azvmextensionevent.AzVMExtensionEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_cloud_type_non_azure(self):
        record = copy.deepcopy(base_record)
        record['com']['cloud_type'] = 'non_azure'
        plugin = azvmextensionevent.AzVMExtensionEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_ext_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['ext'] = None
        plugin = azvmextensionevent.AzVMExtensionEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_record_type_non_vm_instance_view(self):
        record = copy.deepcopy(base_record)
        record['ext']['record_type'] = 'non_vm_instance_view'
        plugin = azvmextensionevent.AzVMExtensionEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_blacklisted_extensions(self):
        record = copy.deepcopy(base_record)
        record['ext']['extensions'] = ['ext01', 'ext02']
        plugin = azvmextensionevent.AzVMExtensionEvent(blacklisted=['ext01'])
        events = list(plugin.eval(record))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['ext']['record_type'],
                         'vm_blacklisted_extension_event')
        self.assertEqual(events[0]['com']['cloud_type'],
                         'azure')
        self.assertEqual(events[0]['com']['record_type'],
                         'vm_blacklisted_extension_event')
        self.assertTrue('reference' in events[0]['com'])
        self.assertIsNotNone(events[0]['com']['description'])
        self.assertIsNotNone(events[0]['com']['recommendation'])

    def test_no_blacklisted_extensions(self):
        record = copy.deepcopy(base_record)
        record['ext']['extensions'] = ['ext01', 'ext02']
        plugin = azvmextensionevent.AzVMExtensionEvent(blacklisted=['ext03'])
        events = list(plugin.eval(record))
        self.assertEqual(len(events), 0)

    def test_whitelisted_extensions(self):
        record = copy.deepcopy(base_record)
        record['ext']['extensions'] = ['ext01', 'ext02']
        plugin = azvmextensionevent.AzVMExtensionEvent(whitelisted=['w_ext01'])
        events = list(plugin.eval(record))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['ext']['record_type'],
                         'vm_unapproved_extension_event')
        self.assertEqual(events[0]['com']['cloud_type'],
                         'azure')
        self.assertEqual(events[0]['com']['record_type'],
                         'vm_unapproved_extension_event')
        self.assertTrue('reference' in events[0]['com'])
        self.assertIsNotNone(events[0]['com']['description'])
        self.assertIsNotNone(events[0]['com']['recommendation'])

    def test_all_whitelisted_extensions(self):
        record = copy.deepcopy(base_record)
        record['ext']['extensions'] = ['ext01', 'ext02']
        plugin = azvmextensionevent. \
            AzVMExtensionEvent(whitelisted=['ext01', 'ext02'])
        events = list(plugin.eval(record))
        self.assertEqual(len(events), 0)

    def test_required_extensions(self):
        record = copy.deepcopy(base_record)
        record['ext']['extensions'] = ['ext01', 'ext02']
        plugin = azvmextensionevent. \
            AzVMExtensionEvent(required=['r_ext01'])
        events = list(plugin.eval(record))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['ext']['record_type'],
                         'vm_required_extension_event')
        self.assertEqual(events[0]['com']['cloud_type'],
                         'azure')
        self.assertEqual(events[0]['com']['record_type'],
                         'vm_required_extension_event')
        self.assertTrue('reference' in events[0]['com'])
        self.assertIsNotNone(events[0]['com']['description'])
        self.assertIsNotNone(events[0]['com']['recommendation'])

    def test_all_required_extensions(self):
        record = copy.deepcopy(base_record)
        record['ext']['extensions'] = ['ext01', 'ext02']
        plugin = azvmextensionevent. \
            AzVMExtensionEvent(required=['ext01', 'ext02'])
        events = list(plugin.eval(record))
        self.assertEqual(len(events), 0)
