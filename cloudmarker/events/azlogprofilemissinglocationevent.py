"""Microsoft Azure Log Profile Missing Location Event.

This module defines the :class:`AzLogProfileMissingLocationEvent` class
that identifies if a log profile which is not enable for all the supported
locations/regions for that subscrition including ``global``. This plugin
works on the log profile properties found in the ``ext`` bucket of
``log_profile`` records.
"""


import logging

from cloudmarker import util

_log = logging.getLogger(__name__)


class AzLogProfileMissingLocationEvent:
    """Azure log profile missing location event plugin."""

    def __init__(self):
        """Create an instance of the class.

        Create an instance of the
        :class:`AzLogProfileMissingLocationEvent`.
        """

    def eval(self, record):
        """Evaluate Azure log profiles for enabled locations.

        Arguments:
            record (dict): An Azure log profile record.

        Yields:
            dict: An event record representing an Azure log profile
            which is not enabled for all locations including global.

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

        yield from _evaluate_log_profile_for_location(com, ext)

    def done(self):
        """Perform cleanup work.

        Currently, this method does nothing. This may change in future.
        """


def _evaluate_log_profile_for_location(com, ext):
    """Evaluate log profile for missing locations.

    Arguments:
        com (dict): Log profile record `com` bucket
        ext (dict): Log profile record `ext` bucket

    Yields:
        dict: An event record representing a log profile which is not enabled
              for all locations.

    """
    available_locations = set(ext.get('subscription_locations'))
    available_locations.add('global')
    missing_locations = list(available_locations - set(ext.get('locations')))
    if not missing_locations:
        return
    yield _get_log_profile_missing_location_event(com, ext, missing_locations)


def _get_log_profile_missing_location_event(com, ext, missing_locations):
    """Generate log profile missing category type event.

    Arguments:
        com (dict): Log profile record `com` bucket
        ext (dict): Log profile record `ext` bucket
        missing_locations (set): Missing location set
    Returns:
        dict: An event record representing log profile which is not enabled
        for all locations.

    """
    friendly_cloud_type = util.friendly_string(com.get('cloud_type'))
    reference = com.get('reference')
    description = (
        '{} log profile {} does not include locations {}.'
        .format(friendly_cloud_type, reference,
                util.friendly_list(missing_locations))
    )
    recommendation = (
        'Check {} log profile {} and enable locations {}.'
        .format(friendly_cloud_type, reference,
                util.friendly_list(missing_locations))
    )
    event_record = {
        # Preserve the extended properties from the log profile
        # record because they provide useful context to locate
        # the log profile that led to the event.
        'ext': util.merge_dicts(ext, {
            'record_type': 'log_profile_missing_location_event',
            'missing_locations': missing_locations
        }),
        'com': {
            'cloud_type': com.get('cloud_type'),
            'record_type': 'log_profile_missing_location_event',
            'reference': reference,
            'description': description,
            'recommendation': recommendation,
        }
    }
    _log.info('Generating log_profile_missing_location_event; %r',
              event_record)
    return event_record
