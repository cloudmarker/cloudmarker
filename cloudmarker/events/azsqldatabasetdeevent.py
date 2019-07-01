"""Microsoft Azure SQL DB Transparent Data Encryption (TDE) event.

This module defines the :class:`AzSQLDatabaseTDEEvent` class that
identifies if a SQL database has TDE disabled . This plugin works on the
SQL DB properties found in the ``ext`` bucket of ``sql_db`` records.
"""


import logging

from cloudmarker import util

_log = logging.getLogger(__name__)


class AzSQLDatabaseTDEEvent:
    """Azure SQL database TDE event plugin."""

    def __init__(self):
        """Create an instance of :class:`AzSQLDatabaseTDEEvent`."""

    def eval(self, record):
        """Evaluate Azure SQL DB for disabled TDE.

        Arguments:
            record (dict): A SQL DB record.

        Yields:
            dict: An event record representing an Azure SQL DB with
            TDE disabled

        """
        com = record.get('com', {})
        if com is None:
            return

        if com.get('cloud_type') != 'azure':
            return

        ext = record.get('ext', {})
        if ext is None:
            return

        if ext.get('record_type') != 'sql_db':
            return

        if ext.get('tde_enabled'):
            return
        yield from _get_sql_db_tde_disabled_event(com, ext)

    def done(self):
        """Perform cleanup work.

        Currently, this method does nothing. This may change in future.
        """


def _get_sql_db_tde_disabled_event(com, ext):
    """Generate SQL DB disabled TDE event.

    Arguments:
        com (dict): SQL DB record `com` bucket
        ext (dict): SQL DB record `ext` bucket
    Returns:
        dict: An event record representing SQL DB with disabled TDE

    """
    friendly_cloud_type = util.friendly_string(com.get('cloud_type'))
    reference = com.get('reference')
    description = (
        '{} SQL DB {} has TDE disabled.'
        .format(friendly_cloud_type, reference)
    )
    recommendation = (
        'Check {} SQL DB {} and enable TDE.'
        .format(friendly_cloud_type, reference)
    )
    event_record = {
        # Preserve the extended properties from the virtual
        # machine record because they provide useful context to
        # locate the virtual machine that led to the event.
        'ext': util.merge_dicts(ext, {
            'record_type': 'sql_db_tde_event'
        }),
        'com': {
            'cloud_type': com.get('cloud_type'),
            'record_type': 'sql_db_tde_event',
            'reference': reference,
            'description': description,
            'recommendation': recommendation,
        }
    }

    _log.info('Generating sql_db_tde_event; %r', event_record)
    yield event_record
