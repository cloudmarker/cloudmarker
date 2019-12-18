"""Microsoft Azure SQL Database plugin to read Azure SQL DB data.

This module defines the :class:`AzSQL` class that retrieves SQL DB
from Microsoft Azure. This module also retrieves the Transparent
Data Encryption (TDE) configuration of the SQL database.
"""


import logging

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.sql import SqlManagementClient
from msrestazure import tools

from cloudmarker import ioworkers, util

_log = logging.getLogger(__name__)


class AzSQL:
    """Azure SQL Database plugin."""

    def __init__(self, tenant, client, secret, processes=4, threads=30,
                 _max_subs=0, _max_recs=0):
        """Create an instance of :class:`AzSQL` plugin.

         Note: The ``_max_subs`` and ``_max_recs`` arguments should be
         used only in the development-test-debug phase. They should not
         be used in production environment. This is why we use the
         convention of beginning their names with underscore.

        Arguments:
            tenant (str): Azure subscription tenant ID.
            client (str): Azure service principal application ID.
            secret (str): Azure service principal password.
            processes (int): Number of worker processes to run.
            threads (int): Number of worker threads to run.
            _max_subs (int): Maximum number of subscriptions to fetch
                data for if the value is greater than 0.
            _max_recs (int): Maximum number of SQL server records
                to fetch for each subscription.

        """
        self._credentials = ServicePrincipalCredentials(
            tenant=tenant,
            client_id=client,
            secret=secret,
        )
        self._tenant = tenant
        self._processes = processes
        self._threads = threads
        self._max_subs = _max_subs
        self._max_recs = _max_recs
        _log.info('Initialized; tenant: %s; processes: %s; threads: %s',
                  self._tenant, self._processes, self._threads)

    def read(self):
        """Return an Azure SQL database record.

        Yields:
            dict: An Azure SQL database record.

        """
        yield from ioworkers.run(self._get_tenant_dbs,
                                 self._get_server_db_details,
                                 self._processes, self._threads,
                                 __name__)

    def _get_tenant_dbs(self):
        """Get SQL DBs from all subscriptions in a tenant.

        The yielded tuples when unpacked would become arguments for
        :meth:`_get_server_db_details`. Each such tuple represents a
        single unit of work that :meth:`_get_server_db_details` can
        work on independently in its own worker thread.

        Yields:
            tuple: A tuple which when unpacked forms valid arguments for
                :meth:`_get_server_db_details`.

        """
        try:
            tenant = self._tenant
            creds = self._credentials
            sub_client = SubscriptionClient(creds)
            sub_list = sub_client.subscriptions.list()

            for sub_index, sub in enumerate(sub_list):
                sub = sub.as_dict()
                _log.info('Found %s', util.outline_az_sub(sub_index,
                                                          sub, tenant))

                yield from self._get_subscription_dbs(sub_index, sub)
                # Break after pulling data for self._max_subs number of
                # subscriptions. Note that if self._max_subs is 0 or less,
                # then the following condition never evaluates to True.
                if sub_index + 1 == self._max_subs:
                    _log.info('Stopping subscriptions fetch due to '
                              '_max_subs: %d; tenant: %s', self._max_subs,
                              tenant)
                    break

        except Exception as e:
            _log.error('Failed to fetch subscriptions; %s; error: %s: %s',
                       util.outline_az_sub(sub_index, sub, tenant),
                       type(e).__name__, e)

    def _get_subscription_dbs(self, sub_index, sub):
        """Get SQL DBs from a single subscrption.

        Arguments:
            sub_index (int): Subscription index (for logging only).
            sub (Subscription): Azure subscription object.

        Yields:
            tuple: A tuple which when unpacked forms valid arguments for
                :meth:`_get_server_db_details`.

        """
        try:
            tenant = self._tenant
            creds = self._credentials
            sub_id = sub.get('subscription_id')
            sql_client = SqlManagementClient(creds, sub_id)
            db_server_list = sql_client.servers.list()

            for server_index, sql_server in enumerate(db_server_list):
                sql_server = sql_server.as_dict()
                server_id = sql_server.get('id')
                server_name = sql_server.get('name')
                _log.info('Found SQL Server #%d: %s; %s',
                          server_index, server_name,
                          util.outline_az_sub(sub_index, sub, tenant))
                rg_name = \
                    tools.parse_resource_id(server_id)['resource_group']
                yield (server_index, server_name, rg_name, sub_index, sub)

                # Break after pulling data for self._max_recs number
                # of SQL servers for a subscriber. Note that if
                # self._max_recs is 0 or less, then the following
                # condition never evaluates to True.
                if server_index + 1 == self._max_recs:
                    _log.info('Stopping SQL server fetch due '
                              'to _max_recs: %d; %s', self._max_recs,
                              util.outline_az_sub(sub_index, sub,
                                                  self._tenant))
                    break
        except Exception as e:
            _log.error('Failed to fetch SQL servers; %s; error: %s: %s',
                       util.outline_az_sub(sub_index, sub, tenant),
                       type(e).__name__, e)

    def _get_server_db_details(self, server_index, server_name, rg_name,
                               sub_index, sub):
        """Get details of all DBs for a SQL server.

        Arguments:
            sub_index (int): Subscription index (for logging only).
            sub (Subscription): Azure subscription object.
            rg_name (str): Resource group name.
            server_index (int): Server index (for logging only).
            server_name (str): Name of the SQL server.

        Yields:
            dict: An Azure SQL server record with TDE configuration.

        """
        _log.info('Working on SQL server #%d: %s; %s', server_index,
                  server_name, util.outline_az_sub(sub_index, sub,
                                                   self._tenant))
        sub_id = sub.get('subscription_id')
        creds = self._credentials
        sql_client = SqlManagementClient(creds, sub_id)
        db_list = sql_client.databases.list_by_server(rg_name, server_name)
        for db_index, db in enumerate(db_list):
            db = db.as_dict()
            sql_db_name = db.get('name')
            tde_config = \
                sql_client.transparent_data_encryptions.get(rg_name,
                                                            server_name,
                                                            sql_db_name)
            tde_config = tde_config.as_dict()
            _log.info('Found sql_db #%d: %s; SQL server #%d: %s; %s',
                      db_index, sql_db_name, server_index, server_name,
                      util.outline_az_sub(sub_index, sub, self._tenant))
            yield from self._process_sql_db_details(sub, db,
                                                    tde_config)

    def done(self):
        """Log a message that this plugin is done."""
        _log.info('Done; tenant: %s; processes: %s; threads: %s',
                  self._tenant, self._processes, self._threads)

    def _process_sql_db_details(self, sub, db, tde_config):
        """Process SQL database record and yield them.

        Arguments:
            db (dict): Raw SQL database record
            tde_config (dict): Raw TDE configuration of a SQL database

        Yields:
            dict: An Azure record of type ``sql_db``.

        """
        db['transparent_data_encryption'] = tde_config
        record = {
            'raw': db,
            'ext': {
                'cloud_type': 'azure',
                'record_type': 'sql_db',
                'subscription_id': sub.get('subscription_id'),
                'subscription_name': sub.get('display_name'),
                'subscription_state': sub.get('state'),
            },
            'com': {
                'cloud_type': 'azure',
                'record_type': 'database',
                'reference': db.get('id')
            }
        }
        record['ext'] = util.merge_dicts(
            record['ext'],
            _get_normalized_tde_config(tde_config),
            )
        yield record


def _get_normalized_tde_config(tde_config):
    """Normalize the TDE configuration of a SQL database.

    Arguments:
        tde_config (dict): Raw TDE configuration of a SQL database

    Returns:
        dict: Normalized TDE configuration

    """
    tde_info = {}
    tde_enabled = False
    tde_status = tde_config.get('status')
    if tde_status == 'Enabled':
        tde_enabled = True
    tde_info['tde_enabled'] = tde_enabled
    return tde_info
