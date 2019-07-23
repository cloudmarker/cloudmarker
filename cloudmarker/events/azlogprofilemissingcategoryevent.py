"""Microsoft Azure Log Profile Missing Category Type Event.

This module defines the :class:`AzLogProfileMissingCategoryEvent` class
that identifies if a log profile which is not enable for all the categories
i.e. Write, Delete and Action. This plugin works on the log profile
properties found in the ``raw`` bucket of ``log_profile`` records.
"""


import logging

from cloudmarker import util

_log = logging.getLogger(__name__)


class AzLogProfileMissingCategoryEvent:
    """Azure log profile missing category event plugin."""

    def __init__(self):
        """Create an instance of the class.

        Create an instance of the
        :class:`AzLogProfileMissingCategoryEvent`.
        """

    def eval(self, record):
        """Evaluate Azure log profiles for enabled categories.

        Arguments:
            record (dict): An Azure log profile record.

        Yields:
            dict: An event record representing an Azure log profile
            which is not enabled for all categories.

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

        raw = record.get('raw', {})
        if raw is None:
            return
        yield from _evaluate_log_profile_for_categories(com, ext, raw)

    def done(self):
        """Perform cleanup work.

        Currently, this method does nothing. This may change in future.
        """


def _evaluate_log_profile_for_categories(com, ext, raw):
    """Evaluate log profile for missing caegories.

    Arguments:
        com (dict): Log profile record `com` bucket
        ext (dict): Log profile record `ext` bucket
        raw (dict): Log profile record `raw` bucket
    Yields:
        dict: An event record representing a log profile which is not enabled
              for all categories.

    """
    categories = set(('Write', 'Delete', 'Action'))
    missing_categories = categories - set(raw.get('categories'))
    if not missing_categories:
        return
    yield _get_log_profile_missing_category_event(com, ext, missing_categories)


def _get_log_profile_missing_category_event(com, ext, missing_categories):
    """Generate log profile missing category type event.

    Arguments:
        com (dict): Log profile record `com` bucket
        ext (dict): Log profile record `ext` bucket
        missing_categories (set): Missing activity set
    Returns:
        dict: An event record representing log profile with missing categories.

    """
    friendly_cloud_type = util.friendly_string(com.get('cloud_type'))
    reference = com.get('reference')
    description = (
        '{} log profile {} does not include categories {}.'
        .format(friendly_cloud_type, reference,
                util.friendly_list(missing_categories))
    )
    recommendation = (
        'Check {} log profile {} and enable categories {}.'
        .format(friendly_cloud_type, reference,
                util.friendly_list(missing_categories))
    )
    event_record = {
        # Preserve the extended properties from the log profile
        # record because they provide useful context to locate
        # the log profile that led to the event.
        'ext': util.merge_dicts(ext, {
            'record_type': 'log_profile_missing_category_event'
        }),
        'com': {
            'cloud_type': com.get('cloud_type'),
            'record_type': 'log_profile_missing_category_event',
            'reference': reference,
            'description': description,
            'recommendation': recommendation,
        }
    }
    _log.info('Generating log_profile_missing_category_event; %r',
              event_record)
    return event_record
