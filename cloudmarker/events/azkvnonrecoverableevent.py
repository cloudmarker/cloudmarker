"""Microsoft Azure Key Vault non-recoverable event.

This module defines the :class:`AzKVNonRecoverableEvent` class
that identifies if a Key Vault is not recoverable. An Azure Key Vault
is recoverable if both ``soft delete`` and ``purge protection`` is
enabled. This plugin works on the Key Vault secret properties found
in the ``ext`` bucket of ``key_vault`` records.
"""


import logging

from cloudmarker import util

_log = logging.getLogger(__name__)


class AzKVNonRecoverableEvent:
    """Azure Key Vault non-recoverable event plugin."""

    def __init__(self):
        """Create an instance of :class:`AzKVNonRecoverableEvent`."""

    def eval(self, record):
        """Evaluate if an Azure Key Vault is recoverable.

        Arguments:
            record (dict): A Key Vault record.

        Yields:
            dict: An event record representing an Azure Key Vault which is
            not recoverable.

        """
        com = record.get('com', {})
        if com is None:
            return

        if com.get('cloud_type') != 'azure':
            return

        ext = record.get('ext', {})
        if ext is None:
            return

        if ext.get('record_type') != 'key_vault':
            return

        if ext.get('recoverable'):
            return
        yield from _get_key_vault_non_recoverable_event(com, ext)

    def done(self):
        """Perform cleanup work.

        Currently, this method does nothing. This may change in future.
        """


def _get_key_vault_non_recoverable_event(com, ext):
    """Generate Key Vault secret expiry event.

    Arguments:
        com (dict): Key Vault record `com` bucket.
        ext (dict): Key Vault record `ext` bucket.

    Returns:
        dict: An event record representing Key Vault which is not
        recoverable.

    """
    friendly_cloud_type = util.friendly_string(com.get('cloud_type'))
    reference = com.get('reference')
    description = (
        '{} Key Vault {} is not recoverable.'
        .format(friendly_cloud_type, reference)
    )
    recommendation = (
        'Check {} Key Vault {} and enable purge protection and soft delete.'
        .format(friendly_cloud_type, reference)
    )
    event_record = {
        # Preserve the extended properties from the key vault
        # record because they provide useful context to
        # locate the key vault secret that led to the event.
        'ext': util.merge_dicts(ext, {
            'record_type': 'key_vault_non_recoverable_event'
        }),
        'com': {
            'cloud_type': com.get('cloud_type'),
            'record_type': 'key_vault_non_recoverable_event',
            'reference': reference,
            'description': description,
            'recommendation': recommendation,
        }
    }

    _log.info('Generating key_vault_non_recoverable_event; %r', event_record)
    yield event_record
