"""Microsoft web app client certificate event.

This module defines the :class:`AzWebAppClientCertEvent` class that
identifies a web app with client certificate (mutual TLS) disabled.
This plugin works on the web apps config properties found in the
``ext`` bucket of ``web_app_config`` records.
"""


import logging

from cloudmarker import util

_log = logging.getLogger(__name__)


class AzWebAppClientCertEvent:
    """Azure web app client certificate event plugin."""

    def __init__(self):
        """Create an instance of :class:`AzWebAppClientCertEvent`."""

    def eval(self, record):
        """Evaluate Azure web app to check if client cert is disabled.

        Arguments:
            record (dict): A web app record.

        Yields:
            dict: An event record representing a web app with client
            certificate (mTLS) disabled.

        """
        com = record.get('com', {})
        if com is None:
            return

        if com.get('cloud_type') != 'azure':
            return

        ext = record.get('ext', {})
        if ext is None:
            return

        if ext.get('record_type') != 'web_app_config':
            return

        if ext.get('client_cert_enabled'):
            return

        yield from _get_azure_web_app_client_cert_event(com, ext)

    def done(self):
        """Perform cleanup work.

        Currently, this method does nothing. This may change in future.
        """


def _get_azure_web_app_client_cert_event(com, ext):
    """Generate Web App client certificate event.

    Arguments:
        com (dict): Azure web app record `com` bucket.
        ext (dict): Azure web app record `ext` bucket.

    Returns:
        dict: An event record representing web app with client
        certificate (mTLS) disabled

    """
    friendly_cloud_type = util.friendly_string(com.get('cloud_type'))
    reference = com.get('reference')
    description = (
        '{} web app {} has client certificate (mTLS) disabled.'
        .format(friendly_cloud_type, reference)
    )
    recommendation = (
        'Check {} web app {} and enable client certificate (mTLS).'
        .format(friendly_cloud_type, reference)
    )

    event_record = {
        # Preserve the extended properties from the web app
        # record because they provide useful context to
        # locate the web app that led to the event.
        'ext': util.merge_dicts(ext, {
            'record_type': 'web_app_client_certificate_event'
        }),
        'com': {
            'cloud_type': com.get('cloud_type'),
            'record_type': 'web_app_client_certificate_event',
            'reference': reference,
            'description': description,
            'recommendation': recommendation,
        }
    }
    _log.info('Generating web_app_client_certificate_event; %r', event_record)
    yield event_record
