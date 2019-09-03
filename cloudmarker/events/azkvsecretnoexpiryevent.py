"""Microsoft Azure Key Vault secret expiry event.

This module defines the :class:`AzKVSecretNoExpiryEvent` class that
identifies if a Key Vault secret without expiry set. This plugin works on the
Key Vault secret properties found in the ``ext`` bucket of ``key_vault_secret``
records.
"""


import logging

from cloudmarker import util

_log = logging.getLogger(__name__)


class AzKVSecretNoExpiryEvent:
    """Azure Key Vault secret expiry event plugin."""

    def __init__(self):
        """Create an instance of :class:`AzKVSecretNoExpiryEvent`."""

    def eval(self, record):
        """Evaluate Azure Key Vault secret for expiry date.

        Arguments:
            record (dict): A Key Vault secret record.

        Yields:
            dict: An event record representing an Azure Key Vault secret
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

        if ext.get('record_type') != 'key_vault_secret':
            return

        if ext.get('enabled') and ext.get('expiry_set'):
            return
        yield from _get_key_vault_secret_no_expiry_event(com, ext)

    def done(self):
        """Perform cleanup work.

        Currently, this method does nothing. This may change in future.
        """


def _get_key_vault_secret_no_expiry_event(com, ext):
    """Generate Key Vault secret expiry event.

    Arguments:
        com (dict): Key Vault secret record `com` bucket.
        ext (dict): Key Vault secret record `ext` bucket.

    Returns:
        dict: An event record representing Key Vault secret with no expiry
        set.

    """
    friendly_cloud_type = util.friendly_string(com.get('cloud_type'))
    reference = com.get('reference')
    description = (
        '{} Key Vault secret {} has has no expiration date set.'
        .format(friendly_cloud_type, reference)
    )
    recommendation = (
        'Check {} Key Vault secret {} and set expiration date.'
        .format(friendly_cloud_type, reference)
    )
    event_record = {
        # Preserve the extended properties from the key vault
        # secret record because they provide useful context to
        # locate the key vault secret that led to the event.
        'ext': util.merge_dicts(ext, {
            'record_type': 'key_vault_secret_no_expiry_event'
        }),
        'com': {
            'cloud_type': com.get('cloud_type'),
            'record_type': 'key_vault_secret_no_expiry_event',
            'reference': reference,
            'description': description,
            'recommendation': recommendation,
        }
    }

    _log.info('Generating key_vault_secret_no_expiry_event; %r', event_record)
    yield event_record
