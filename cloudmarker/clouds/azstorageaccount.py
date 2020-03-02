"""Microsoft Azure storage accounts plugin to read Azure storage accounts data.

This module defines the :class:`AzStorageAccount` class that retrieves storage
accounts data from Microsoft Azure.

"""


import logging

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.storage import StorageManagementClient
from msrestazure import tools

from cloudmarker import ioworkers, util

_log = logging.getLogger(__name__)


class AzStorageAccount:
    """Azure storage account plugin."""

    def __init__(self, tenant, client, secret, processes=4,
                 threads=30, _max_subs=0, _max_recs=0):
        """Create an instance of :class:`AzStorageAccount` plugin.

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
            _max_recs (int): Maximum number of storage accounts records
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
        """Return an Azure storage account record.

        Yields:
            dict: An Azure storage account record.

        """
        yield from ioworkers.run(self._get_tenant_storage_accounts,
                                 self._get_storage_account_properties,
                                 self._processes, self._threads,
                                 __name__)

    def _get_tenant_storage_accounts(self):
        """Get storage accounts from all subscriptions in a tenant.

        The yielded tuples when unpacked would become arguments for
        :meth:` _get_storage_account_properties`. Each such tuple represents a
        single unit of work that :meth:` _get_storage_account_properties` can
        work on independently in its own worker thread.

        Yields:
            tuple: A tuple which when unpacked forms valid arguments for
                :meth:` _get_storage_account_properties`.

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
                yield from self._get_subscription_storage_accounts(sub_index,
                                                                   sub)
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

    def _get_subscription_storage_accounts(self, sub_index, sub):
        """Get storage accounts from a single subscrption.

        Yields:
            tuple: A tuple which when unpacked forms valid arguments for
                :meth:` _get_storage_account_properties`.

        """
        try:
            tenant = self._tenant
            creds = self._credentials
            sub_id = sub.get('subscription_id')
            client = StorageManagementClient(creds, sub_id)
            storage_account_list = client.storage_accounts.list()

            for t in enumerate(storage_account_list):
                (storage_account_index, storage_account) = t
                storage_account = storage_account.as_dict()

                _log.info('Found storage account #%d: %s; %s',
                          storage_account_index, storage_account.get('name'),
                          util.outline_az_sub(sub_index, sub, tenant))
                yield (storage_account_index, storage_account, sub_index, sub)

                if storage_account_index + 1 == self._max_recs:
                    _log.info('Stopping storage accounts fetch due '
                              'to _max_recs: %d; %s', self._max_recs,
                              util.outline_az_sub(sub_index, sub, tenant))
                    break
        except Exception as e:
            _log.error('Failed to fetch storage accounts; %s; error: %s: %s',
                       util.outline_az_sub(sub_index, sub, tenant),
                       type(e).__name__, e)

    def _get_storage_account_properties(self, storage_account_index,
                                        storage_account, sub_index, sub):
        """Get storage account records with property details.

        Arguments:
            storage_account_index (int): Storage account index (logging only).
            storage_account (dict): Raw storage account record.
            sub_index (int): Subscription index (for logging only).
            sub (Subscription): Azure subscription object.

        Yields:
            dict: An Azure storage account record with property details.

        """
        act_name = storage_account.get('name')
        _log.info('Working on storage account #%d: %s; %s',
                  storage_account_index,
                  act_name,
                  util.outline_az_sub(sub_index, sub, self._tenant))
        try:
            creds = self._credentials
            sub_id = sub.get('subscription_id')
            client = StorageManagementClient(creds, sub_id)
            account_id = storage_account.get('id')
            rg_name = tools.parse_resource_id(account_id)['resource_group']

            properties = client.storage_accounts.get_properties(rg_name,
                                                                act_name)
            properties = properties.as_dict()
            yield _process_storage_account_properties(storage_account_index,
                                                      storage_account,
                                                      properties,
                                                      sub_index,
                                                      sub,
                                                      self._tenant)
        except Exception as e:
            _log.error('Failed to fetch properties for storage accounts'
                       '#%d:%s; %s; error: %s: %s', storage_account_index,
                       act_name,
                       util.outline_az_sub(sub_index, sub, self._tenant),
                       type(e).__name__, e)

    def done(self):
        """Log a message that this plugin is done."""
        _log.info('Done; tenant: %s; processes: %s; threads: %s',
                  self._tenant, self._processes, self._threads)


def _process_storage_account_properties(storage_account_index,
                                        storage_account,
                                        storage_account_properties,
                                        sub_index,
                                        sub,
                                        tenant):
    """Get storage account records with property details.

    Arguments:
        storage_account_index (int): Storage account index (logging only).
        storage_account (dict): Raw storage account record.
        storage_account_properties (dict): Storage account properties record.
        sub_index (int): Subscription index (for logging only).
        sub (Subscription): Azure subscription object.
        tenant (str): Azure tenant ID.

    Yields:
        dict: An Azure record of type ``storage_account_properties``.

    """
    storage_account['properties'] = storage_account_properties
    default_network_access_allowed = True
    if storage_account['network_rule_set'].get('default_action') != 'Allow':
        default_network_access_allowed = False
    record = {
        'raw': storage_account,
        'ext': {
            'cloud_type': 'azure',
            'record_type': 'storage_account_properties',
            'secure_transfer_required': storage_account_properties.get(
                'enable_https_traffic_only'
            ),
            'default_network_access_allowed': default_network_access_allowed,
            'subscription_id': sub.get('subscription_id'),
            'subscription_name': sub.get('display_name'),
            'subscription_state': sub.get('state'),
        },
        'com': {
            'cloud_type': 'azure',
            'reference': storage_account.get('id')
        }
    }
    _log.info('Found storage_account_properties #%d: %s; %s',
              storage_account_index, storage_account.get('name'),
              util.outline_az_sub(sub_index, sub, tenant))

    return record
