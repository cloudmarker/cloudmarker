"""Microsoft Azure Key Vault key expiry event.

This module defines the :class:`AzKVKeyNoExpiryEvent` class that
identifies Key Vault keys without expiry set. This plugin works on the
Key Vault key properties found in the ``ext`` bucket of ``key_vault_key``
records.
"""


import logging

from cloudmarker import util

_log = logging.getLogger(__name__)


class AzKVKeyNoExpiryEvent:
    """Azure Key Vault key expiry event plugin."""

    def __init__(self):
        """Create an instance of :class:`AzKVKeyNoExpiryEvent`."""

    def eval(self, record):
        """Evaluate Azure Key Vault key for expiry date.

        Arguments:
            record (dict): A Key Vault key record.

        Yields:
            dict: An event record representing an Azure Key Vault keys
            without expiry date.

        """
        com = record.get('com', {})
        if com is None:
            return

        if com.get('cloud_type') != 'azure':
            return

        ext = record.get('ext', {})
        if ext is None:
            return

        if ext.get('record_type') != 'key_vault_key':
            return

        if ext.get('enabled') and ext.get('expiry_set'):
            return
        yield from _get_key_vault_key_no_expiry_event(com, ext)

    def done(self):
        """Perform cleanup work.

        Currently, this method does nothing. This may change in future.
        """


def _get_key_vault_key_no_expiry_event(com, ext):
    """Generate Key Vault key expiry event.

    Arguments:
        com (dict): Key Vault key record `com` bucket.
        ext (dict): Key Vault key record `ext` bucket.

    Returns:
        dict: An event record representing Key Vault key with no expiry
        set.

    """
    friendly_cloud_type = util.friendly_string(com.get('cloud_type'))
    reference = com.get('reference')
    description = (
        '{} Key Vault key {} has has no expiry set.'
        .format(friendly_cloud_type, reference)
    )
    recommendation = (
        'Check {} Key Vault key {} and set expiry.'
        .format(friendly_cloud_type, reference)
    )
    event_record = {
        # Preserve the extended properties from the key vault
        # key record because they provide useful context to
        # locate the key vault key that led to the event.
        'ext': util.merge_dicts(ext, {
            'record_type': 'key_vault_key_no_expiry_event'
        }),
        'com': {
            'cloud_type': com.get('cloud_type'),
            'record_type': 'key_vault_key_no_expiry_event',
            'reference': reference,
            'description': description,
            'recommendation': recommendation,
        }
    }

    _log.info('Generating key_vault_key_no_expiry_event; %r', event_record)
    yield event_record
