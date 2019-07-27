"""Microsoft web app HTTPS event.

This module defines the :class:`AzWebAppHttpsEvent` class that identifies
a web app with HTTPS only traffic disabled. This plugin works on the web
apps config properties found in the ``ext`` bucket of ``web_app_config``
records.
"""


import logging

from cloudmarker import util

_log = logging.getLogger(__name__)


class AzWebAppHttpsEvent:
    """Azure web app HTTPS event plugin."""

    def __init__(self):
        """Create an instance of :class:`AzWebAppHttpsEvent`."""

    def eval(self, record):
        """Evaluate Azure web app to check for HTTPS only config.

        Arguments:
            record (dict): A web app record.

        Yields:
            dict: An event record representing a web app with HTTPS
            only traffic disabled.

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

        if ext.get('https_only'):
            return

        yield from _get_azure_web_app_https_event(com, ext)

    def done(self):
        """Perform cleanup work.

        Currently, this method does nothing. This may change in future.
        """


def _get_azure_web_app_https_event(com, ext):
    """Generate Web App HTTPS event.

    Arguments:
        com (dict): Azure web app record `com` bucket.
        ext (dict): Azure web app record `ext` bucket.

    Returns:
        dict: An event record representing web apps not using
        HTTPS only traffic.

    """
    friendly_cloud_type = util.friendly_string(com.get('cloud_type'))
    reference = com.get('reference')
    description = (
        '{} web app {} has HTTPS only traffic disabled.'
        .format(friendly_cloud_type, reference)
    )
    recommendation = (
        'Check {} web app {} and enable HTTPS only traffic.'
        .format(friendly_cloud_type, reference)
    )

    event_record = {
        # Preserve the extended properties from the web app
        # record because they provide useful context to
        # locate the web app that led to the event.
        'ext': util.merge_dicts(ext, {
            'record_type': 'web_app_https_event'
        }),
        'com': {
            'cloud_type': com.get('cloud_type'),
            'record_type': 'web_app_https_event',
            'reference': reference,
            'description': description,
            'recommendation': recommendation,
        }
    }
    _log.info('Generating web_app_https_event; %r', event_record)
    yield event_record
