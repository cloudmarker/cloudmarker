"""Microsoft Azure VM OS disk encryption event.

This module defines the :class:`AzVMOSDiskEncryptionEvent` class that
identifies an unencrypted Azure OS disk. This plugin works on the
virtual machine properties found in the ``com`` bucket of
``virtual_machine`` records.
"""


import logging

from cloudmarker import util

_log = logging.getLogger(__name__)


class AzVMOSDiskEncryptionEvent:
    """Az VM OS disk encryption event plugin."""

    def __init__(self):
        """Create an instance of :class:`AzVMOSDiskEncryptionEvent`."""

    def eval(self, record):
        """Evaluate Azure virtual machine to check for unencrypted OS disk.

        Arguments:
            record (dict): A virtual machine record.

        Yields:
            dict: An event record representing an unencrypted OS disk
            of an Azure virtual machine

        """
        # If 'com' bucket is missing, we have a malformed record. Log a
        # warning and ignore it.
        com = record.get('com')
        if com is None:
            _log.warning('Virtual machine record is missing \'com\' key: %r',
                         record)
            return

        # This plugin understands compute rule records only,
        # so ignore  any other record types.
        common_record_type = com.get('record_type')

        if common_record_type != 'compute':
            return

        # If 'ext' bucket is missing, we have a malformed record. Log a
        # warning and ignore it.
        ext = record.get('ext')
        if ext is None:
            _log.warning('Virtual machine record is missing \'ext\' key: %r',
                         record)
            return
        os_disk_encrypted = ext.get('os_disk_encrypted')

        if os_disk_encrypted:
            return
        if com.get('cloud_type') == 'azure':
            yield from _get_azure_vm_os_disk_encryption_event(
                com, ext, record.get('raw'))

    def done(self):
        """Perform cleanup work.

        Currently, this method does nothing. This may change in future.
        """


def _get_azure_vm_os_disk_encryption_event(com, ext, raw):
    """Evaluate Azure VM for unencrypted OS disks.

    Arguments:
        com (dict): Virtual machine record `com` bucket
        ext (dict): Virtual machine record `ext` bucket
        raw (dict): Virtual machine record `raw` bucket
    Returns:
        dict: An event record representing unencrypted OS disk

    """
    friendly_cloud_type = util.friendly_string(com.get('cloud_type'))
    os_disk_name = raw.get('storage_profile').get('os_disk').get('name')
    reference = com.get('reference')
    description = (
        '{} virtual machine {} has unencrypted OS disk {}'
        .format(friendly_cloud_type, reference, os_disk_name)
    )
    recommendation = (
        'Check {} virtual machine {} and encrypt OS disk {}'
        .format(friendly_cloud_type, reference, os_disk_name)
    )

    event_record = {
        # Preserve the extended properties from the virtual
        # machine record because they provide useful context to
        # locate the virtual machine that led to the event.
        'ext': util.merge_dicts(ext, {
            'record_type': 'vm_os_disk_encryption_event'
        }),
        'com': {
            'cloud_type': com.get('cloud_type'),
            'record_type': 'vm_os_disk_encryption_event',
            'reference': reference,
            'description': description,
            'recommendation': recommendation,
        }
    }
    _log.info('Generating vm_os_disk_encryption_event; %r', event_record)
    yield event_record
