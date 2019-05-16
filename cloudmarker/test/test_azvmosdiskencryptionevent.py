"""Tests for AzVMOSDiskEncryptionEventTest plugin."""


import copy
import unittest

from cloudmarker.events import azvmosdiskencryptionevent

base_record = {
    'ext':  {
        'record_type': 'vm_instance_view',
        'os_disk_encrypted':  True
    },
    'com':  {
        'cloud_type':  'azure'
    }
}

base_raw_bucket = {
        "storage_profile": {
            "os_disk": {
                "name": "myVM_OS_DISK"
            }
        }
}


class AzVMOSDiskEncryptionEventTest(unittest.TestCase):
    """Tests for AzVMOSDiskEncryptionEventTest plugin."""

    def test_com_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['com'] = None
        plugin = azvmosdiskencryptionevent.AzVMOSDiskEncryptionEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_record_type_non_compute(self):
        record = copy.deepcopy(base_record)
        record['com']['record_type'] = 'non_compute'
        plugin = azvmosdiskencryptionevent.AzVMOSDiskEncryptionEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_ext_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['ext'] = None
        plugin = azvmosdiskencryptionevent.AzVMOSDiskEncryptionEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_os_disk_encrypted(self):
        record = copy.deepcopy(base_record)
        plugin = azvmosdiskencryptionevent.AzVMOSDiskEncryptionEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_cloud_type_non_azure(self):
        record = copy.deepcopy(base_record)
        record['ext']['os_disk_encrypted'] = False
        record['com']['cloud_type'] = 'non_azure'
        plugin = azvmosdiskencryptionevent.AzVMOSDiskEncryptionEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_unencrypted_os_disk(self):
        record = copy.deepcopy(base_record)
        record['raw'] = copy.deepcopy(base_raw_bucket)
        record['ext']['os_disk_encrypted'] = False
        plugin = azvmosdiskencryptionevent.AzVMOSDiskEncryptionEvent()
        events = list(plugin.eval(record))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['ext']['record_type'],
                         'vm_os_disk_encryption_event')
        self.assertEqual(events[0]['com']['record_type'],
                         'vm_os_disk_encryption_event')
