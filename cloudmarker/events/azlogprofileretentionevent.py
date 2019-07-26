"""Microsoft Azure Log Profile Retention Event.

This module defines the :class:`AzLogProfileRetentionEvent` class that
identifies if an Azure log profile's retention policy is configured for
less than the minimum number of days than required. This plugin works
properties found in the ``ext`` bucket of ``log_profile`` records.
"""


import logging

from cloudmarker import util

_log = logging.getLogger(__name__)


class AzLogProfileRetentionEvent:
    """Azure log profile retention event plugin."""

    def __init__(self, _min_retention_days=365):
        """Create an instance of :class:`AzLogProfileRetentionEvent`.

        Arguments:
            _min_retention_days (int): Minimum required
                                    retention days.

        """
        self._min_retention_days = _min_retention_days
        _log.info("Initialized; minimum retention days: %d",
                  self._min_retention_days)

    def eval(self, record):
        """Evaluate Azure log profiles for retention policy.

        Arguments:
            record (dict): An Azure log profile record.

        Yields:
            dict: An event record representing an Azure log profile
            with retention set to less than the required days.

        """
        com = record.get('com', {})
        if com is None:
            return

        if com.get('cloud_type') != 'azure':
            return

        if com.get('record_type') != 'log_profile':
            return

        ext = record.get('ext', {})
        if ext is None:
            return

        if ext['retention_enabled']:
            if ext['retention_days'] < self._min_retention_days:
                yield from _get_log_profile_retention_event(
                    com, ext, self._min_retention_days)
        else:
            if ext['retention_days'] != 0:
                yield from _get_log_profile_retention_event(
                    com, ext, self._min_retention_days)

    def done(self):
        """Perform cleanup work.

        Currently, this method does nothing. This may change in future.
        """


def _get_log_profile_retention_event(com, ext, min_retention_days):
    """Generate log profile retention event.

    Arguments:
        com (dict): Log profile record `com` bucket
        ext (dict): Log profile record `ext` bucket
        min_retention_days (int): Minimum required retention days.

    Returns:
        dict: An event record representing log profile with retention
             policy configured for less number of days than required.

    """
    friendly_cloud_type = util.friendly_string(com.get('cloud_type'))
    reference = com.get('reference')
    description = (
        '{} log profile {} has log retention set to less than {} days.'
        .format(friendly_cloud_type, reference, min_retention_days)
    )
    recommendation = (
        'Check {} log profile {} and set log retention to more than {} days.'
        .format(friendly_cloud_type, reference, min_retention_days)
    )
    event_record = {
        # Preserve the extended properties from the virtual
        # machine record because they provide useful context to
        # locate the virtual machine that led to the event.
        'ext': util.merge_dicts(ext, {
            'record_type': 'log_profile_retention_event'
        }),
        'com': {
            'cloud_type': com.get('cloud_type'),
            'record_type': 'log_profile_retention_event',
            'reference': reference,
            'description': description,
            'recommendation': recommendation,
        }
    }

    _log.info('Generating log_profile_retention_event; %r', event_record)
    yield event_record
