"""Microsoft storage account allow trusted services event.

This module defines the :class:`AzStorageAccountAllowTrustedServicesEvent`
class that identifies a storage account with network access set to
denied to Microsoft Azure services. This plugin works on the storage
account properties record found in the ``ext`` bucket of
``storage_account_properties`` records.
"""


import logging

from cloudmarker import util

_log = logging.getLogger(__name__)


class AzStorageAccountAllowTrustedServicesEvent:
    """Azure storage account allow trusted services event plugin."""

    def __init__(self):
        """Initialize :class:`AzStorageAccountAllowTrustedServicesEvent`."""

    def eval(self, record):
        """Evaluate Azure storage account for trusted services access.

        Arguments:
            record (dict): A storage account record.

        Yields:
            dict: An event record representing a storage account with Azure
            services not allowed to access the storage account.

        """
        com = record.get('com')
        com = record.get('com', {})
        if com is None:
            return
        if com.get('cloud_type') != 'azure':
            return
        ext = record.get('ext')
        if ext is None:
            return
        if ext.get('record_type') != 'storage_account_properties':
            return

        trusted_services_allowed = \
            ext.get('trusted_services_allowed')
        if trusted_services_allowed is False:
            yield from _get_az_storage_account_allow_trusted_services_event(
                com, ext)

    def done(self):
        """Perform cleanup work.

        Currently, this method does nothing. This may change in future.

        """


def _get_az_storage_account_allow_trusted_services_event(com, ext):
    """Generate Azure storage account allow trusted services event.

    Arguments:
        com (dict): Azure storage account record `com` bucket.
        ext (dict): Azure storage account record `ext` bucket.

    Returns:
        dict: An event record representing storage accounts with Azure
        services not allowed access.

    """
    friendly_cloud_type = util.friendly_string(com.get('cloud_type'))
    reference = com.get('reference')

    description = (
        '{} storage account {} does not allow access to Azure services.'
        .format(friendly_cloud_type, reference)
    )
    recommendation = (
        'Check {} storage account {} and allow access to Azure services.'
        .format(friendly_cloud_type, reference)
    )

    event_record = {
        # Preserve the  properties from the storage account
        # record because they provide useful context to
        # locate the storage account that led to the event.
        'ext': util.merge_dicts(ext, {
            'record_type': 'storage_account_allow_trusted_services_event'
        }),
        'com': {
            'cloud_type': com.get('cloud_type'),
            'record_type': 'storage_account_allow_trusted_services_event',
            'reference': reference,
            'description': description,
            'recommendation': recommendation,
        }
    }

    _log.info('Generating storage_account_allow_trusted_services_event; %r',
              event_record)
    yield event_record
