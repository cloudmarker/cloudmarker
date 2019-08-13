"""Microsoft storage account secure transfer event.

This module defines the :class:`AzStorageAccountEvent` class that identifies
a storage account with secure transfer enabled  not set to true .
This plugin works on the storage account properties record found in the
``ext`` bucket of ``storage_account_properties`` records.

"""


import logging

from cloudmarker import util

_log = logging.getLogger(__name__)


class AzStorageAccountEvent:
    """Azure storage account secure transfer enabled check event plugin."""

    def __init__(self):
        """Create an instance of :class:`AzStorageAccountEvent`."""

    def eval(self, record):
        """Evaluate Azure storage account for insecure transfer enabled status.

        Arguments:
            record (dict): A storage account record.

        Yields:
            dict: An event record representing a storage account with secure
            transfer not enabled property.

        """
        com = record.get('com')
        ext = record.get('ext')
        if ext.get('record_type') != 'storage_account_properties':
            return

        sec_transf_required = ext.get('secure_transfer_required')

        if sec_transf_required is False:
            yield from _get_az_storage_account_secure_transfer_event(
                com, ext)

    def done(self):
        """Perform cleanup work.

        Currently, this method does nothing. This may change in future.

        """


def _get_az_storage_account_secure_transfer_event(com, ext):
    """Evaluate Azure storage account property for insecure transfer enabled.

    Arguments:
        com (dict): Azure storage account record `com` bucket
        ext (dict): Azure storage account record `ext` bucket
        raw (dict): Azure storage account record `raw` bucket

    Returns:
        dict: An event record representing storage accounts with  secure
        transfer enabled set to false

    """
    friendly_cloud_type = util.friendly_string(com.get('cloud_type'))
    reference = com.get('reference')

    description = (
        '{} storage account {} does not require secure transfer.'
        .format(friendly_cloud_type, reference)
    )
    recommendation = (
        'Check {} storage account {} and ensure that it requires '
        'secure transfer.'.format(friendly_cloud_type, reference)
    )

    event_record = {
        # Preserve the  properties from the storage account
        # record because they provide useful context to
        # locate the storage account that led to the event.
        'ext': util.merge_dicts(ext, {
            'record_type': 'storage_account_event'
        }),
        'com': {
            'cloud_type': com.get('cloud_type'),
            'record_type': 'storage_account_event',
            'reference': reference,
            'description': description,
            'recommendation': recommendation,
        }
    }
    _log.info('Generating storage_account_event; %r',
              event_record)
    yield event_record
