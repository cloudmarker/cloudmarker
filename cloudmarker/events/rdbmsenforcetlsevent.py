"""RDBMS Enforce TLS/SSL Event.

This module defines the :class:`RDBMSEnforceTLSEvent` class that
identifies RDBMS servers which have TLS/SSL connection enforcement
disabled. This plugin works on the  properties found in the ``com``
bucket of ``rdbms`` records.
"""


import logging

from cloudmarker import util

_log = logging.getLogger(__name__)


class RDBMSEnforceTLSEvent:
    """Az RDBMS TLS/SSL enforcement event plugin."""

    def __init__(self):
        """Create an instance of :class:`RDBMSEnforceTLSEvent`."""

    def eval(self, record):
        """Evaluate RDBMS servers for TLS connection enforcement.

        Arguments:
            record (dict): An RDBMS record.

        Yields:
            dict: An event record representing an RDBMS where TLS
            connection enforcement is disabled

        """
        com = record.get('com', {})
        if com is None:
            return

        if com.get('record_type') != 'rdbms':
            return

        ext = record.get('ext', {})
        if ext is None:
            return

        # True, None, missing key or any other value will not
        # genarated an event. An event will be generated only if
        # the value of `tls_enforced` is False.
        if com.get('tls_enforced') is False:
            yield from _get_rdbms_tls_enforcement_event(
                com, ext)

    def done(self):
        """Perform cleanup work.

        Currently, this method does nothing. This may change in future.
        """


def _get_rdbms_tls_enforcement_event(com, ext):
    """Generate event for TLS enforcement disabled.

    Arguments:
        com (dict): RDBMS record `com` bucket
        ext (dict): RDBMS record `ext` bucket
    Returns:
        dict: An event record representing RDBMS with SSL
        connection enforcement disabled

    """
    friendly_cloud_type = util.friendly_string(com.get('cloud_type'))
    friendly_rdbms_type = util.friendly_string(ext.get('record_type'))

    reference = com.get('reference')
    description = (
        '{} {} {} has TLS/SSL enforcement disabled.'
        .format(friendly_cloud_type, friendly_rdbms_type, reference)
    )
    recommendation = (
        'Check {} {} {} and enable TLS/SSL enforcement.'
        .format(friendly_cloud_type, friendly_rdbms_type, reference)
    )

    event_record = {
        # Preserve the extended properties from the RDBMS
        # record because they provide useful context to
        # locate the RDBMS that led to the event.
        'ext': util.merge_dicts(ext, {
            'record_type': 'rdbms_enforce_tls_event'
        }),
        'com': {
            'cloud_type': com.get('cloud_type'),
            'record_type': 'rdbms_enforce_tls_event',
            'reference': reference,
            'description': description,
            'recommendation': recommendation,
        }
    }

    _log.info('Generating rdbms_enforce_tls_event; %r', event_record)
    yield event_record
