"""Tests for AzAzVMDataDiskEncryptionEventTest plugin."""


import copy
import random
import unittest

from cloudmarker.events import azvmdatadiskencryptionevent

base_record = {
    'ext':  {
        'record_type': 'vm_instance_view',
        'all_data_disks_encrypted':  True
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
        },
        "instance_view": {
            "disks": [
                {
                    "name": "myVM_OS_DISK",
                    "encryption_settings": [
                        {
                            "enabled": True
                        }
                    ]
                }
            ]
        }
}

base_unencrypted_data_disk = {
    "name": "myVM_DATA_DISK_0",
    "encryption_settings": [
        {
            "enabled": False
        }
    ]
}


class AzAzVMDataDiskEncryptionEventTest(unittest.TestCase):
    """Tests for AzVMDataDiskEncryptionEvent plugin."""

    def test_ext_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['ext'] = None
        plugin = azvmdatadiskencryptionevent.AzVMDataDiskEncryptionEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_record_type_non_vm_instance_view(self):
        record = copy.deepcopy(base_record)
        record['ext']['record_type'] = 'non_vm_instance_view'
        plugin = azvmdatadiskencryptionevent.AzVMDataDiskEncryptionEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_instance_view_missing(self):
        record = copy.deepcopy(base_record)
        record['raw'] = copy.deepcopy(base_raw_bucket)
        record['raw']['instance_view'] = None
        record['ext']['all_data_disks_encrypted'] = False
        plugin = azvmdatadiskencryptionevent.AzVMDataDiskEncryptionEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_all_data_disks_encrypted(self):
        record = copy.deepcopy(base_record)
        plugin = azvmdatadiskencryptionevent.AzVMDataDiskEncryptionEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_com_bucket_missing(self):
        record = copy.deepcopy(base_record)
        record['ext']['all_data_disks_encrypted'] = False
        record['com'] = None
        plugin = azvmdatadiskencryptionevent.AzVMDataDiskEncryptionEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_cloud_type_non_azure(self):
        record = copy.deepcopy(base_record)
        record['ext']['all_data_disks_encrypted'] = False
        record['com']['cloud_type'] = 'non_azure'
        plugin = azvmdatadiskencryptionevent.AzVMDataDiskEncryptionEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_single_unencrypted_data_disk(self):
        record = copy.deepcopy(base_record)
        record['raw'] = copy.deepcopy(base_raw_bucket)
        record['ext']['all_data_disks_encrypted'] = False
        record['raw']['instance_view']['disks'].append(
            copy.deepcopy(base_unencrypted_data_disk))
        plugin = azvmdatadiskencryptionevent.AzVMDataDiskEncryptionEvent()
        events = list(plugin.eval(record))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['ext']['record_type'],
                         'vm_data_disk_encryption_event')
        self.assertEqual(events[0]['com']['record_type'],
                         'vm_data_disk_encryption_event')

    def test_single_encrypted_data_disk(self):
        record = copy.deepcopy(base_record)
        record['raw'] = copy.deepcopy(base_raw_bucket)
        record['ext']['all_data_disks_encrypted'] = False
        encrypted_data_disk = copy.deepcopy(base_unencrypted_data_disk)
        encrypted_data_disk['encryption_settings'][0]['enabled'] = True
        record['raw']['instance_view']['disks'].append(encrypted_data_disk)
        plugin = azvmdatadiskencryptionevent.AzVMDataDiskEncryptionEvent()
        events = list(plugin.eval(record))
        self.assertEqual(len(events), 0)

    def test_multiple_unencrypted_data_disk(self):
        record = copy.deepcopy(base_record)
        record['raw'] = copy.deepcopy(base_raw_bucket)
        record['ext']['all_data_disks_encrypted'] = False
        unencrypted_data_disks = random.randint(1, 5)
        for x in range(unencrypted_data_disks):
            unencrypted_data_disk = copy.deepcopy(base_unencrypted_data_disk)
            unencrypted_data_disk['name'] = 'data_disk' + str(x)
            record['raw']['instance_view']['disks'].append(
                unencrypted_data_disk)
        plugin = azvmdatadiskencryptionevent.AzVMDataDiskEncryptionEvent()
        events = list(plugin.eval(record))
        self.assertEqual(len(events), unencrypted_data_disks)

    def test_mixtype_unencrypted_data_disk(self):
        record = copy.deepcopy(base_record)
        record['raw'] = copy.deepcopy(base_raw_bucket)
        record['ext']['all_data_disks_encrypted'] = False
        unencrypted_data_disk = copy.deepcopy(base_unencrypted_data_disk)
        unencrypted_data_disk['encryption_settings'] = None
        record['raw']['instance_view']['disks'].append(unencrypted_data_disk)
        disabled_encrypted_data_disk = copy.deepcopy(
            base_unencrypted_data_disk)
        record['raw']['instance_view']['disks'].append(
            disabled_encrypted_data_disk)
        plugin = azvmdatadiskencryptionevent.AzVMDataDiskEncryptionEvent()
        events = list(plugin.eval(record))
        self.assertEqual(len(events), 2)
