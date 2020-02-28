"""Microsoft Azure Postgres Connection Throttling event.

This module defines the :class:`AzPostgresConnectionThrottlingEvent` class
that identifies Postgre SQL servers which connection throttling configuration
disabled. This plugin works on the  properties found in the ``com``
bucket of ``postgresql_server`` records.
"""


import logging

from cloudmarker import util

_log = logging.getLogger(__name__)


class AzPostgresConnectionThrottlingEvent:
    """Az Postgres connection throttling event plugin."""

    def __init__(self):
        """Create instance of :class:`AzPostgresConnectionThrottlingEvent`."""

    def eval(self, record):
        """Evaluate Postgres for connection throttling.

        Arguments:
            record (dict): An RDBMS record.

        Yields:
            dict: An event record representing a Postgres where
            connection throttling is disabled

        """
        com = record.get('com', {})
        if com is None:
            return

        if com.get('cloud_type') != 'azure':
            return

        if com.get('record_type') != 'rdbms':
            return

        ext = record.get('ext', {})
        if ext is None:
            return

        if ext.get('record_type') != 'postgresql_server':
            return

        # True, None, missing key or any other value will not
        # genarated an event. An event will be generated only if
        # the value of `postgresql_server` is False.
        if ext.get('connection_throttling_enabled') is False:
            yield from _get_postgres_connection_throttling_disabled_event(
                com, ext)

    def done(self):
        """Perform cleanup work.

        Currently, this method does nothing. This may change in future.
        """


def _get_postgres_connection_throttling_disabled_event(com, ext):
    """Generate event for Postgres connection throttling disabled.

    Arguments:
        com (dict): Postgres record `com` bucket
        ext (dict): Postgres record `ext` bucket
    Returns:
        dict: An event record representing Postgres server
        with connection throttling disabled

    """
    friendly_cloud_type = util.friendly_string(com.get('cloud_type'))
    friendly_rdbms_type = util.friendly_string(ext.get('record_type'))

    reference = com.get('reference')
    description = (
        '{} {} {} has connection throttling disabled.'
        .format(friendly_cloud_type, friendly_rdbms_type, reference)
    )
    recommendation = (
        'Check {} {} {} and enable connection throttling.'
        .format(friendly_cloud_type, friendly_rdbms_type, reference)
    )

    event_record = {
        # Preserve the extended properties from the RDBMS
        # record because they provide useful context to
        # locate the RDBMS that led to the event.
        'ext': util.merge_dicts(ext, {
            'record_type': 'postgres_connection_throttling_event'
        }),
        'com': {
            'cloud_type': com.get('cloud_type'),
            'record_type': 'postgres_connection_throttling_event',
            'reference': reference,
            'description': description,
            'recommendation': recommendation,
        }
    }

    _log.info('Generating postgres_connection_throttling_event; %r',
              event_record)
    yield event_record
