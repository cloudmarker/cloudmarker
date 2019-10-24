"""Microsoft Azure Postgres plugin to read Azure Postgres data.

This module defines the :class:`AzPostgres` class that retrieves Postgre SQL
data from Microsoft Azure.
"""


import logging

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.rdbms.postgresql import PostgreSQLManagementClient
from azure.mgmt.resource import SubscriptionClient
from msrestazure import tools
from msrestazure.azure_exceptions import CloudError

from cloudmarker import ioworkers, util

_log = logging.getLogger(__name__)


class AzPostgres:
    """Azure Postgres plugin."""

    def __init__(self, tenant, client, secret, processes=4, threads=30,
                 _max_subs=0, _max_recs=0):
        """Create an instance of :class:`AzPostgres` plugin.

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
            _max_recs (int): Maximum number of Postgres records
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
        """Return an Azure Postgres record.

        Yields:
            dict: An Azure Postgres record.

        """
        yield from ioworkers.run(self._get_tenant_postgres,
                                 self._get_postgres_server_details,
                                 self._processes, self._threads,
                                 __name__)

    def _get_tenant_postgres(self):
        """Get Postgres details from all subscriptions in a tenant.

        The yielded tuples when unpacked would become arguments for
        :meth:`_get_postgres_server_details`. Each such tuple represents
        a single unit of work that :meth:`_get_postgres_details` can
        work on independently in its own worker thread.

        Yields:
            tuple: A tuple which when unpacked forms valid arguments for
                :meth:`_get_postgres_server_details`.

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

                yield from self._get_subscription_postgres_servers(sub_index,
                                                                   sub)
                # Break after pulling data for self._max_subs number of
                # subscriptions. Note that if self._max_subs is 0 or less,
                # then the following condition never evaluates to True.
                if sub_index + 1 == self._max_subs:
                    _log.info('Stopping subscriptions fetch due to '
                              '_max_subs: %d; tenant: %s', self._max_subs,
                              tenant)
                    break

        except CloudError as e:
            _log.error('Failed to fetch subscriptions; %s; error: %s: %s',
                       util.outline_az_sub(sub_index, sub, tenant),
                       type(e).__name__, e)

    def _get_subscription_postgres_servers(self, sub_index, sub):
        """Get Postgres servers from a single subscrption.

        Arguments:
            sub_index (int): Subscription index (for logging only).
            sub (Subscription): Azure subscription object.

        Yields:
            tuple: A tuple which when unpacked forms valid arguments for
                :meth:`_get_postgres_details`.

        """
        try:
            tenant = self._tenant
            creds = self._credentials
            sub_id = sub.get('subscription_id')
            postgres_client = PostgreSQLManagementClient(creds, sub_id)
            db_server_list = postgres_client.servers.list()

            for server_index, postgres_server in enumerate(db_server_list):
                postgres_server = postgres_server.as_dict()
                server_id = postgres_server.get('id')
                server_name = postgres_server.get('name')
                _log.info('Found Postgres Server #%d: %s; %s',
                          server_index, server_name,
                          util.outline_az_sub(sub_index, sub, tenant))
                rg_name = \
                    tools.parse_resource_id(server_id)['resource_group']
                yield (server_index, server_name, rg_name, sub_index, sub)

                # Break after pulling data for self._max_recs number
                # of Postgres servers for a subscriber. Note that if
                # self._max_recs is 0 or less, then the following
                # condition never evaluates to True.
                if server_index + 1 == self._max_recs:
                    _log.info('Stopping Postgres server fetch due '
                              'to _max_recs: %d; %s', self._max_recs,
                              util.outline_az_sub(sub_index, sub,
                                                  self._tenant))
                    break
        except CloudError as e:
            _log.error('Failed to fetch Postgres servers; %s; error: %s: %s',
                       util.outline_az_sub(sub_index, sub, tenant),
                       type(e).__name__, e)

    def _get_postgres_server_details(self, server_index, server_name, rg_name,
                                     sub_index, sub):
        """Get details Postgres server.

        Arguments:
            sub_index (int): Subscription index (for logging only).
            sub (Subscription): Azure subscription object.
            rg_name (str): Resource group name.
            server_index (int): Server index (for logging only).
            server_name (str): Name of the Postgres server.

        Yields:
            dict: An Azure Postgres server record with configuration.

        """
        _log.info('Working on Postgres server #%d: %s; %s', server_index,
                  server_name, util.outline_az_sub(sub_index, sub,
                                                   self._tenant))
        sub_id = sub.get('subscription_id')
        creds = self._credentials
        postgres_client = PostgreSQLManagementClient(creds, sub_id)
        server_details = postgres_client.servers.get(rg_name, server_name)
        server_details = server_details.as_dict()
        server_configuration_list = \
            postgres_client.configurations.list_by_server(rg_name, server_name)
        configurations, derived_configs = \
            self._get_postgres_server_configuration(server_configuration_list)
        yield from self._process_postgres_server_details(sub, server_details,
                                                         configurations,
                                                         derived_configs)

    def done(self):
        """Log a message that this plugin is done."""
        _log.info('Done; tenant: %s; processes: %s; threads: %s',
                  self._tenant, self._processes, self._threads)

    def _get_postgres_server_configuration(self, server_configuration_list):
        """Iterate over list of Postgres servers and normalize them.

        Arguments:
            server_configuration_list (iterator): An iterator instance of
                                                  Postgres server configuration

        Returns:
            list: A list of Postgres server configurations.
            dict: A dictionary of Postgres server derived configurations.

        """
        derived_configs = {}
        configuration_list = []
        # These are the configuration names which will be processed to
        # have a derived value. Also, name of these configuration will
        # be suffixed with `_enabled` if the `data_type` is Boolean.
        config_names_to_derive = ['log_checkpoints', 'log_connections',
                                  'log_disconnections', 'log_duration',
                                  'connection_throttling',
                                  'log_retention_days']
        for _, configuration in enumerate(server_configuration_list):
            config = configuration.as_dict()
            configuration_list.append(config)
            if config['name'] in config_names_to_derive:
                if config['data_type'] == 'Boolean':
                    derived_configs[config['name'] + '_enabled'] = \
                        False
                    if config['value'].lower() == 'on':
                        derived_configs[config['name'] + '_enabled'] = \
                            True
                elif config['data_type'] == 'Integer':
                    derived_configs[config['name']] = int(config['value'])
        return configuration_list, derived_configs

    def _process_postgres_server_details(self, sub, server, configuration,
                                         derived_configurations):
        """Process Postgres server details and configuration and yield them.

        Arguments:
            server (dict): Raw Postgres server record.
            configuration (list): Raw Postgres server configuration.
            derived_configurations (dict): Derived Postgres server
                                           configuration.

        Yields:
            dict: An Azure record of type ``rdbms``.

        """
        server['configuration'] = configuration
        ssl_enforcement = server.get('raw', {}).get('ssl_enforcement')
        ssl_connection_enabled = (ssl_enforcement == 'Enabled')
        record = {
            'raw': server,
            'ext': {
                'cloud_type': 'azure',
                'record_type': 'postgresql_server',
                'subscription_id': sub.get('subscription_id'),
                'subscription_name': sub.get('display_name'),
                'subscription_state': sub.get('state'),

            },
            'com': {
                'cloud_type': 'azure',
                'record_type': 'rdbms',
                'reference': server.get('id'),
                'tls_enforced': ssl_connection_enabled,
            }
        }
        record['ext'] = util.merge_dicts(
            record['ext'], derived_configurations
            )
        yield record
