"""Microsoft Azure log profile event.

This module defines the :class:`AzLogProfileEvent` class that creates
events for Azure subscriptions with missing log profiles.
"""


import logging

from cloudmarker import util

_log = logging.getLogger(__name__)


class AzLogProfileEvent:
    """Azure log profile event plugin."""

    def __init__(self):
        """Create an instance of :class:`AzLogProfileEvent`."""

    def eval(self, record):
        """Evaluate Azure subscription for missing log profile.

        Arguments:
            record (dict): Azure ``log_profile_missing`` record.

        Yields:
            dict: An event record for every ``log_profile_missing``
            record.

        """
        com = record.get('com', {})
        if com is None:
            return

        ext = record.get('ext', {})
        if ext is None:
            return

        if ext.get('record_type') == 'log_profile_missing':
            yield from _get_log_profile_missing_event(com, ext)

    def done(self):
        """Perform cleanup work.

        Currently, this method does nothing. This may change in future.
        """


def _get_log_profile_missing_event(com, ext):
    """Create an event record for missing log profile.

    Arguments:
        com (dict): The `com` bucket of a ``log_profile_missing`` record.
        ext (dict): The `ext` bucket of a ``log_profile_missing`` record.

    Returns:
        dict: An event record representing log profile missing for a
        subscription.

    """
    friendly_cloud_type = util.friendly_string(com.get('cloud_type'))
    reference = com.get('reference')
    description = (
        '{} subscription {} has log profile missing.'
        .format(friendly_cloud_type, reference)
    )
    recommendation = (
        'Check {} subscription {} and create a log profile.'
        .format(friendly_cloud_type, reference)
    )
    event_record = {
        # Preserve the extended properties from the virtual
        # machine record because they provide useful context to
        # locate the virtual machine that led to the event.
        'ext': util.merge_dicts(ext, {
            'record_type': 'log_profile_event'
        }),
        'com': {
            'cloud_type': com.get('cloud_type'),
            'record_type': 'log_profile_event',
            'reference': reference,
            'description': description,
            'recommendation': recommendation,
        }
    }

    _log.info('Generating log_profile_event; %r', event_record)
    yield event_record
