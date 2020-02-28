"""Microsoft Azure Postgres Log Retention Days event.

This module defines the :class:`AzPostgresLogRetentionDaysEvent` class
that identifies Postgre SQL servers which have log retention days set
below the desired minimum value. This plugin works on the  properties
found in the ``com`` bucket of ``postgresql_server`` records.
"""


import logging

from cloudmarker import util

_log = logging.getLogger(__name__)


class AzPostgresLogRetentionDaysEvent:
    """Az Postgres log retention days event plugin."""

    def __init__(self, _min_log_retention_days=3):
        """Create instance of :class:`AzPostgresLogRetentionDaysEvent`."""
        self._min_log_retention_days = _min_log_retention_days
        _log.info("Initialized; minimum log retention days: %d",
                  self._min_log_retention_days)

    def eval(self, record):
        """Evaluate Postgres for log retention days.

        Arguments:
            record (dict): An RDBMS record.
            _min_log_retention_days (int): Minimum required log retention days.

        Yields:
            dict: An event record representing a Postgres where
            log retention days is set below desired minimum

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
        log_retention_days = ext.get('log_retention_days')

        if log_retention_days < self._min_log_retention_days:
            yield from _get_postgres_log_retention_days_event(
                com, ext, self._min_log_retention_days)

    def done(self):
        """Perform cleanup work.

        Currently, this method does nothing. This may change in future.
        """


def _get_postgres_log_retention_days_event(com, ext, min_log_retention_days):
    """Generate event for Postgres log retention days set below minimum.

    Arguments:
        com (dict): Postgres record `com` bucket
        ext (dict): Postgres record `ext` bucket
        min_log_retention_days (int): Minimum log retention days
    Returns:
        dict: An event record representing Postgres server
        with log retention days set below desired minimum.

    """
    friendly_cloud_type = util.friendly_string(com.get('cloud_type'))
    friendly_rdbms_type = util.friendly_string(ext.get('record_type'))

    reference = com.get('reference')
    description = (
        '{} {} {} has log retention days set below desired minimum value.'
        .format(friendly_cloud_type, friendly_rdbms_type, reference)
    )
    recommendation = (
        'Check {} {} {} and set log retention days to minimum of {} days.'
        .format(friendly_cloud_type, friendly_rdbms_type, reference,
                min_log_retention_days)
    )

    event_record = {
        # Preserve the extended properties from the RDBMS
        # record because they provide useful context to
        # locate the RDBMS that led to the event.
        'ext': util.merge_dicts(ext, {
            'record_type': 'postgres_log_retention_days_event'
        }),
        'com': {
            'cloud_type': com.get('cloud_type'),
            'record_type': 'postgres_log_retention_days_event',
            'reference': reference,
            'description': description,
            'recommendation': recommendation,
        }
    }

    _log.info('Generating postgres_log_retention_days_event; %r',
              event_record)
    yield event_record
