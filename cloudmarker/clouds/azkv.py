"""Microsoft Azure Key Vault plugin to read Key Vault and associated resources.

This module defines the :class:`AzKV` class that retrieves Key Vault
from Microsoft Azure. This module also retrieves the keys and secret
attributes stored within a Key Vault.
"""


import itertools
import logging

from azure.common.credentials import ServicePrincipalCredentials
from azure.keyvault import KeyVaultAuthentication, KeyVaultClient
from azure.keyvault.models import KeyVaultErrorException
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.mgmt.resource import SubscriptionClient
from msrestazure import tools
from msrestazure.azure_exceptions import CloudError

from cloudmarker import ioworkers, util

_log = logging.getLogger(__name__)


class AzKV:
    """Azure Key Vault plugin."""

    def __init__(self, tenant, client, secret, processes=4, threads=30,
                 _max_subs=0, _max_recs=0):
        """Create an instance of :class:`AzKV` plugin.

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
            _max_recs (int): Maximum number of Key Vault records
                to fetch for each subscription.

        """
        self._credentials = ServicePrincipalCredentials(
            tenant=tenant,
            client_id=client,
            secret=secret,
        )
        self._key_vault_credentials = ServicePrincipalCredentials(
            tenant=tenant,
            client_id=client,
            secret=secret,
            resource="https://vault.azure.net",
        )
        self._tenant = tenant
        self._processes = processes
        self._threads = threads
        self._max_subs = _max_subs
        self._max_recs = _max_recs
        _log.info('Initialized; tenant: %s; processes: %s; threads: %s',
                  self._tenant, self._processes, self._threads)

    def read(self):
        """Return an Azure Key Vault record.

        Yields:
            dict: An Azure Key Vault and associated resource record.

        """
        yield from ioworkers.run(self._get_tenant_kvs,
                                 self._process_key_vault,
                                 self._processes, self._threads,
                                 __name__)

    def _get_tenant_kvs(self):
        """Get Key Vaults from all subscriptions in a tenant.

        The yielded tuples when unpacked would become arguments for
        :meth:`_process_key_vault`. Each such tuple represents a
        single unit of work that :meth:`_process_key_vault` can
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

                yield from self._get_subscription_kvs(sub_index, sub)
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

    def _get_subscription_kvs(self, sub_index, sub):
        """Get Key Vaults from a single subscrption.

        Arguments:
            sub_index (int): Subscription index (for logging only).
            sub (Subscription): Azure subscription object.

        Yields:
            tuple: A tuple which when unpacked forms valid arguments for
                :meth:`_process_key_vault`.

        """
        try:
            tenant = self._tenant
            creds = self._credentials
            subscription_id = sub.get('subscription_id')
            key_vault_mgmt_client = KeyVaultManagementClient(creds,
                                                             subscription_id)
            key_vault_list = key_vault_mgmt_client.vaults.list()

            for key_vault_index, key_vault in enumerate(key_vault_list):
                key_vault = key_vault.as_dict()
                key_vault_name = key_vault.get('name')
                key_vault_id = key_vault.get('id')
                _log.info('Found key_vault #%d: %s; %s',
                          key_vault_index, key_vault_name,
                          util.outline_az_sub(sub_index, sub, tenant))
                rg_name = \
                    tools.parse_resource_id(key_vault_id)['resource_group']

                yield (key_vault_index, key_vault_name,
                       rg_name, sub_index, sub)

                # Break after pulling data for self._max_recs number
                # of Key Vault for a subscriber. Note that if
                # self._max_recs is 0 or less, then the following
                # condition never evaluates to True.
                if key_vault_index + 1 == self._max_recs:
                    _log.info('Stopping Key Vault fetch due '
                              'to _max_recs: %d; %s', self._max_recs,
                              util.outline_az_sub(sub_index, sub,
                                                  self._tenant))
                    break
        except CloudError as e:
            _log.error('Failed to fetch Key Vault; %s; error: %s: %s',
                       util.outline_az_sub(sub_index, sub, tenant),
                       type(e).__name__, e)

    def _process_key_vault(self, key_vault_index, key_vault_name, rg_name,
                           sub_index, sub):
        """Get details of Key Vault in management and data plane.

        Arguments:
            sub_index (int): Subscription index (for logging only).
            sub (Subscription): Azure subscription object.
            rg_name (str): Resource group name.
            key_vault_index (int): Key Vault index (for logging only).
            key_vault_name (str): Name of the Key Vault.

        Yields:
            dict: An Azure Key Vault server record.

        """
        def _auth_callback(server, resource, scope):
            credentials = self._key_vault_credentials
            token = credentials.token
            return token['token_type'], token['access_token']

        _log.info('Working on key_vault #%d: %s; %s', key_vault_index,
                  key_vault_name, util.outline_az_sub(sub_index, sub,
                                                      self._tenant))
        subscription_id = sub.get('subscription_id')
        creds = self._credentials
        key_vault_mgmt_client = KeyVaultManagementClient(creds,
                                                         subscription_id)
        key_vault_details = key_vault_mgmt_client.vaults.get(rg_name,
                                                             key_vault_name)
        yield from _get_normalized_key_vault_record(key_vault_details, sub)
        try:
            kv_client = \
                KeyVaultClient(KeyVaultAuthentication(_auth_callback))

            secrets = \
                kv_client.get_secrets(key_vault_details.properties.vault_uri)

            keys = \
                kv_client.get_keys(key_vault_details.properties.vault_uri)

            # Retrieve data using each iterator.
            for record in itertools.chain(
                    _get_data_record(secrets, 'key_vault_secret',
                                     sub_index, sub, self._tenant),
                    _get_data_record(keys, 'key_vault_key',
                                     sub_index, sub, self._tenant),
            ):
                yield record

        except CloudError as e:
            _log.error('Failed to fetch key vault details; %s; error: %s: %s',
                       util.outline_az_sub(sub_index, sub, self._tenant),
                       type(e).__name__, e)

    def done(self):
        """Log a message that this plugin is done."""
        _log.info('Done; tenant: %s; processes: %s; threads: %s',
                  self._tenant, self._processes, self._threads)


def _get_data_record(iterator, azure_record_type, sub_index, sub,
                     tenant):
    """Normalize the Key Vault data plane record.

    Arguments:
        iterator: An iterator like instance of
            :class:`msrest.serialization.Model` objects.
        azure_record_type (str): Record type name.
        sub_index (int): Subscription index (for logging only).
        sub (Subscription): Azure subscription object.
        tenant (str): Azure tenant ID (for logging only).

    Returns:
        dict: Normalized Key Vault data plane record.

    """
    try:
        for i, v in enumerate(iterator):
            raw_record = v.as_dict()
            reference = raw_record.get('id')
            if azure_record_type == 'key_vault_key':
                reference = raw_record.get('kid')
            expiry_set = raw_record['attributes'].get('expires') is not None
            enabled = raw_record['attributes'].get('enabled')
            record = {
                'raw': raw_record,
                'ext': {
                    'cloud_type': 'azure',
                    'expiry_set': expiry_set,
                    'enabled': enabled,
                    'record_type': azure_record_type,
                    'reference': reference,
                    'subscription_id': sub.get('subscription_id'),
                    'subscription_name': sub.get('display_name'),
                    'subscription_state': sub.get('state'),
                },
                'com': {
                    'cloud_type': 'azure',
                    'record_type': azure_record_type,
                    'reference': reference,
                }
            }

            _log.info('Found %s #%d: %s; %s', azure_record_type, i, reference,
                      util.outline_az_sub(sub_index, sub, tenant))
            yield record

    except KeyVaultErrorException as e:
        _log.error('Failed to fetch details for %s; %s; error: %s: %s',
                   azure_record_type,
                   util.outline_az_sub(sub_index, sub, tenant),
                   type(e).__name__, e)


def _get_normalized_key_vault_record(key_vault_record, sub):
    """Normalize the Key Vault details.

    Arguments:
        key_vault_record (dict): Raw Key Vault record.
        sub (Subscription): Azure subscription object.

    Returns:
        dict: Normalized Key Vault details.

    """
    raw_record = key_vault_record.as_dict()
    enable_soft_delete = False
    if raw_record['properties'].get('enable_soft_delete'):
        enable_soft_delete = raw_record['properties'].get('enable_soft_delete')
    enable_purge_protection = False
    if raw_record['properties'].get('enable_purge_protection'):
        enable_purge_protection = raw_record['properties']. \
                                  get('enable_purge_protection')
    record = {
        'raw': raw_record,
        'ext': {
            'cloud_type': 'azure',
            'record_type': 'key_vault',
            'enable_soft_delete': enable_soft_delete,
            'enable_purge_protection': enable_purge_protection,
            'recoverable': enable_purge_protection and enable_soft_delete,
            'subscription_id': sub.get('subscription_id'),
            'subscription_name': sub.get('display_name'),
            'subscription_state': sub.get('state'),
        },
        'com': {
            'cloud_type': 'azure',
            'record_type': 'key_vault',
            'reference': raw_record.get('id', {}),
        }
    }
    yield record
