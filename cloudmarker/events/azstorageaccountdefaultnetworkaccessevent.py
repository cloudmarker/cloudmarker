"""Microsoft storage account default network access event.

This module defines the :class:`AzStorageAccountDefaultNetworkAccessEvent`
class that identifies a storage account with default network access set to
`Allow`. This plugin works on the storage account properties record
found in the ``ext`` bucket of ``storage_account_properties`` records.
"""


import logging

from cloudmarker import util

_log = logging.getLogger(__name__)


class AzStorageAccountDefaultNetworkAccessEvent:
    """Azure storage account default network access event plugin."""

    def __init__(self):
        """Initialize :class:`AzStorageAccountDefaultNetworkAccessEvent`."""

    def eval(self, record):
        """Evaluate Azure storage account for default network access.

        Arguments:
            record (dict): A storage account record.

        Yields:
            dict: An event record representing a storage account with default
            network access allowed.

        """
        com = record.get('com')
        ext = record.get('ext')
        if ext.get('record_type') != 'storage_account_properties':
            return

        default_network_access_allowed = \
            ext.get('default_network_access_allowed')
        if default_network_access_allowed is True:
            yield from _get_az_storage_account_default_network_access_event(
                com, ext)

    def done(self):
        """Perform cleanup work.

        Currently, this method does nothing. This may change in future.

        """


def _get_az_storage_account_default_network_access_event(com, ext):
    """Generate Azure storage account default network access event.

    Arguments:
        com (dict): Azure storage account record `com` bucket.
        ext (dict): Azure storage account record `ext` bucket.

    Returns:
        dict: An event record representing storage accounts with default
        network access set to allowed.

    """
    friendly_cloud_type = util.friendly_string(com.get('cloud_type'))
    reference = com.get('reference')

    description = (
        '{} storage account {} has default network access set to allowed.'
        .format(friendly_cloud_type, reference)
    )
    recommendation = (
        'Check {} storage account {} and set default network access to deny.'
        .format(friendly_cloud_type, reference)
    )

    event_record = {
        # Preserve the  properties from the storage account
        # record because they provide useful context to
        # locate the storage account that led to the event.
        'ext': util.merge_dicts(ext, {
            'record_type': 'storage_account_default_network_access_event'
        }),
        'com': {
            'cloud_type': com.get('cloud_type'),
            'record_type': 'storage_account_default_network_access_event',
            'reference': reference,
            'description': description,
            'recommendation': recommendation,
        }
    }

    _log.info('Generating storage_account_default_network_access_event; %r',
              event_record)
    yield event_record
