"""Microsoft Azure cloud plugin to read Azure infrastructure data.

This module defines the :class:`AzCloud` class that retrieves data
from Microsoft Azure.
"""


import logging

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.rdbms.mysql import MySQLManagementClient
from azure.mgmt.resource import ResourceManagementClient, SubscriptionClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.web import WebSiteManagementClient

from cloudmarker import ioworkers, util

_log = logging.getLogger(__name__)


class AzCloud:
    """Azure cloud plugin."""

    def __init__(self, tenant, client, secret, processes=4,
                 threads=30, _max_subs=0, _max_recs=0):
        """Create an instance of :class:`AzCloud` plugin.

         Note: The ``_max_subs`` and ``_max_recs`` arguments should be
         used only in the development-test-debug phase. They should not
         be used in production environment. This is why we use the
         convention of beginning their names with underscore.

        Arguments:
            tenant (str): Azure subscription tenant ID.
            client (str): Azure service principal application ID.
            secret (str): Azure service principal password.
            processes (int): Number of processes to launch.
            threads (int): Number of threads to launch in each process.
            _max_subs (int): Maximum number of subscriptions to fetch
                data for if the value is greater than 0.
            _max_recs (int): Maximum number of records of each type to
                fetch under each subscription.

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
        """Return an Azure cloud infrastructure configuration record.

        Yields:
            dict: An Azure cloud infrastructure configuration record.

        """
        yield from ioworkers.run(self._get_subscriptions,
                                 self._get_resources,
                                 self._processes, self._threads,
                                 __name__)

    def _get_subscriptions(self):
        """Generate tuples of record types and subscriptions.

        The yielded tuples when unpacked would become arguments for
        :meth:`_get_resources`. Each such tuple represents a single unit
        of work that :meth:`_get_resources` can work on independently in
        its own worker thread.

        Yields:
            tuple: A tuple which when unpacked forms valid arguments for
                :meth:`_get_resources`.

        """
        try:
            sub_client = SubscriptionClient(self._credentials)
            sub_list = sub_client.subscriptions.list()

            record_types = ('virtual_machine', 'app_gateway', 'lb', 'nic',
                            'nsg', 'public_ip', 'storage_account',
                            'resource_group', 'mysql_server',
                            'web_apps', 'subscription')

            tenant = self._tenant
            for sub_index, sub in enumerate(sub_list):
                sub = sub.as_dict()
                _log.info('Found %s', util.outline_az_sub(sub_index,
                                                          sub, tenant))
                # Each record type for each subscription is a unit of
                # work that would be fed to _get_resources().

                for record_type in record_types:
                    yield (record_type, sub_index, sub)

                # Break after pulling data for self._max_subs number of
                # subscriptions. Note that if self._max_subs is 0 or less,
                # then the following condition never evaluates to True.
                if sub_index + 1 == self._max_subs:
                    _log.info('Stopping subscriptions fetch due to '
                              '_max_subs: %d; tenant: %s', self._max_subs,
                              self._tenant)
                    break

        except Exception as e:
            _log.error('Failed to fetch subscriptions; %s; error: %s: %s',
                       util.outline_az_sub(sub_index, sub, tenant),
                       type(e).__name__, e)

    def _get_resources(self, record_type, sub_index, sub):
        """Return an Azure cloud infrastructure configuration record.

        Arguments:
            record_type (str): Record type name.
            sub_index (int): Subscription index (for logging only).
            sub (Subscription): Azure subscription object.

        Yields:
            dict: An Azure cloud infrastructure configuration record.

        """
        _log.info('Working on %s list; %s', record_type,
                  util.outline_az_sub(sub_index, sub, self._tenant))

        if record_type == 'subscription':
            record = {
                'raw': sub,
                'ext': {
                    'cloud_type': 'azure',
                    'record_type': record_type,
                    'subscription_id': sub.get('subscription_id'),
                    'tenant_id': self._tenant,
                    'subscription_name': sub.get('display_name'),
                    'subscription_state': sub.get('state'),
                },
                'com': {
                    'cloud_type': 'azure',
                    'record_type': 'subscription'
                }
            }

            yield record
            return

        try:
            iterator = \
                _get_resource_iterator(record_type, self._credentials,
                                       sub_index, sub, self._tenant)

            yield from _get_record(iterator, record_type, self._max_recs,
                                   sub_index, sub, self._tenant)
        except Exception as e:
            _log.error('Failed to fetch details for %s; %s; error: %s: %s',
                       record_type,
                       util.outline_az_sub(sub_index, sub, self._tenant),
                       type(e).__name__, e)

    def done(self):
        """Log a message that this plugin is done."""
        _log.info('Done; tenant: %s; processes: %s; threads: %s',
                  self._tenant, self._processes, self._threads)


def _get_resource_iterator(record_type, credentials,
                           sub_index, sub, tenant):
    """Return an appropriate iterator for ``record_type``.

    Arguments:
        record_type (str): Record type.
        credentials (ServicePrincipalCredentials): Credentials.
        sub_index (int): Subscription index (for logging only).
        sub (Subscription): Subscription object.
        tenant (str): Tenant ID (for logging only).

    Returns:
        msrest.paging.Paged: An Azure paging container for iterating
            over a list of Azure resource objects.

    """
    sub_id = sub.get('subscription_id')

    if record_type == 'virtual_machine':
        client = ComputeManagementClient(credentials, sub_id)
        return client.virtual_machines.list_all()

    if record_type == 'app_gateway':
        client = NetworkManagementClient(credentials, sub_id)
        return client.application_gateways.list_all()

    if record_type == 'lb':
        client = NetworkManagementClient(credentials, sub_id)
        return client.load_balancers.list_all()

    if record_type == 'nic':
        client = NetworkManagementClient(credentials, sub_id)
        return client.network_interfaces.list_all()

    if record_type == 'nsg':
        client = NetworkManagementClient(credentials, sub_id)
        return client.network_security_groups.list_all()

    if record_type == 'public_ip':
        client = NetworkManagementClient(credentials, sub_id)
        return client.public_ip_addresses.list_all()

    if record_type == 'storage_account':
        client = StorageManagementClient(credentials, sub_id)
        return client.storage_accounts.list()

    if record_type == 'resource_group':
        client = ResourceManagementClient(credentials, sub_id)
        return client.resource_groups.list()

    if record_type == 'mysql_server':
        client = MySQLManagementClient(credentials, sub_id)
        return client.servers.list()

    if record_type == 'web_apps':
        client = WebSiteManagementClient(credentials, sub_id)
        return client.web_apps.list()

    # If control reaches here, there is a bug in this plugin. It means
    # there is a value in record_types variable in _get_subscriptions
    # that is not handled in the above if-statements.
    _log.warning('Unrecognized record_type: %s; %s', record_type,
                 util.outline_az_sub(sub_index, sub, tenant))
    return None


def _get_record(iterator, azure_record_type, max_recs,
                sub_index, sub, tenant):
    """Process a list of :class:`msrest.serialization.Model` objects.

    Arguments:
        iterator: An iterator like instance of
            :class:`msrest.serialization.Model` objects.
        azure_record_type (str): Type of record as per Azure vocabulary.
        max_recs (int): Maximum number of records to fetch.
        sub_index (int): Subscription index (for logging only).
        sub (Subscription): Azure subscription model object.
        tenant (str): Azure tenant ID (for logging only).

    Yields:
        dict: An Azure record of type ``record_type``.

    """
    # Dictionary to map Azure record types to common record types.
    record_type_map = {
        'virtual_machine': 'compute',
        'mysql_server': 'rdbms',
    }

    for i, v in enumerate(iterator):
        raw_record = v.as_dict()
        record = {
            'raw': raw_record,
            'ext': {
                'cloud_type': 'azure',
                'record_type': azure_record_type,
                'subscription_id': sub.get('subscription_id'),
                'tenant_id': tenant,
                'subscription_name': sub.get('display_name'),
                'subscription_state': sub.get('state'),
            },
            'com': {
                'cloud_type': 'azure',
                'record_type': record_type_map.get(azure_record_type)
            }
        }

        _log.info('Found %s #%d: %s; %s', azure_record_type, i,
                  raw_record.get('name'),
                  util.outline_az_sub(sub_index, sub, tenant))

        # For every security rule found in an NSG, generate a
        # separate security rule (firewall rule) record to maintain
        # parity with separate records for separate firewall rules
        # in GCP.
        if azure_record_type == 'nsg':
            yield from _get_normalized_firewall_rules(
                record, sub_index, sub, tenant)

        if azure_record_type in ['mysql_server']:
            yield from _get_normalized_rdbms_record(record)
            return

        yield record

        if i + 1 == max_recs:
            _log.info('Stopping %s fetch due to _max_recs: %d; %s',
                      azure_record_type, max_recs,
                      util.outline_az_sub(sub_index, sub, tenant))
            break


def _get_normalized_firewall_rules(nsg_record, sub_index, sub, tenant):
    """Split a network security group (NSG) into multiple firewall rules.

    An Azure NSG record contains a top-level key named
    ``security_rules`` whose value is a list of security rules.
    In order to make it easier to write event plugins to detect security
    issues in an NSG, we generate a new firewall rule record for each
    security rule found in the NSG.

    Arguments:
        nsg_record (dict): NSG record generated by this plugin.
        sub_index (int): Subscription index (for logging only)
        sub (Subscription): Azure subscription object (for logging only)
        tenant (str): Azure tenant ID (for logging only)

    Yields:
        dict: A normalized firewall rule record with ``com`` bucket
            populated with firewall rule properties in common notation.

    """
    security_rules = nsg_record.get('raw', {}).get('security_rules')
    nsg_name = nsg_record.get('raw', {}).get('name')

    if security_rules is None:
        _log.warning('Found NSG without security_rules; name: %s; %s',
                     nsg_name, util.outline_az_sub(sub_index, sub, tenant))
        return

    for i, security_rule in enumerate(security_rules):
        record = {
            'raw': security_rule,

            # Preserve the extended properties from NSG record.
            'ext': util.merge_dicts(nsg_record.get('ext'), {

                # Set extended properties specific to a security rule.
                'record_type': 'security_rule',
                'nsg_id': nsg_record.get('raw', {}).get('id'),
                'security_rule_id': security_rule.get('id'),
            }),

            'com': {
                'cloud_type': 'azure',
                'record_type': 'firewall_rule',
                'reference': security_rule.get('id'),

                'enabled':
                    _get_normalized_firewall_state(security_rule),

                'direction':
                    _get_normalized_firewall_direction(security_rule),

                'access':
                    _get_normalized_firewall_access(security_rule),

                'source_addresses':
                    _get_normalized_firewall_source_addresses(security_rule),

                'protocol':
                    _get_normalized_firewall_protocol(security_rule),

                'destination_ports':
                    _get_normalized_firewall_destination_ports(security_rule),
            }
        }

        _log.info('Found security_rule #%d: %s; %s',
                  i, security_rule.get('name'),
                  util.outline_az_sub(sub_index, sub, tenant))
        yield record


def _get_normalized_firewall_state(security_rule):
    rule_name = security_rule.get('name')
    state = security_rule.get('provisioning_state')

    if state is None:
        _log.warning('Found security rule without provisioning_state; '
                     'name: %s', rule_name)
        return None

    return state.lower() == 'succeeded'


def _get_normalized_firewall_direction(security_rule):
    rule_name = security_rule.get('name')
    direction = security_rule.get('direction')

    if direction is None:
        _log.warning('Found security rule without direction; name: %s',
                     rule_name)
        return None

    direction = direction.lower()

    if direction == 'inbound':
        return 'in'

    if direction == 'outbound':
        return 'out'

    _log.warning('Found unknown direction in security rule; '
                 'direction: %s; name: %s', direction, rule_name)
    return direction


def _get_normalized_firewall_access(security_rule):
    rule_name = security_rule.get('name')
    access = security_rule.get('access')

    if access is None:
        _log.warning('Found security rule without access; name: %s',
                     rule_name)
        return None

    access = access.lower()

    if access in ('allow', 'deny'):
        return access

    _log.warning('Found unknown access in security rule; '
                 'access: %s; name: %s', access, rule_name)
    return access


def _get_normalized_firewall_source_addresses(security_rule):
    all_prefixes = []

    prefix = security_rule.get('source_address_prefix')
    if prefix is not None:
        all_prefixes.append(prefix)

    prefixes = security_rule.get('source_address_prefixes')
    if prefixes is not None:
        all_prefixes.extend(prefixes)

    source_addresses = []
    for prefix in all_prefixes:
        if prefix in ('*', 'Internet'):
            source_addresses.append('0.0.0.0/0')
        else:
            source_addresses.append(prefix)

    return source_addresses


def _get_normalized_firewall_protocol(security_rule):
    rule_name = security_rule.get('name')
    protocol = security_rule.get('protocol')

    if protocol is None:
        _log.warning('Found security rule without protocol; name: %s',
                     rule_name)
        return None

    protocol = protocol.lower()
    if protocol == '*':
        return 'all'
    return protocol


def _get_normalized_firewall_destination_ports(security_rule):
    all_ports = []

    port = security_rule.get('destination_port_range')
    if port not in (None, ''):
        all_ports.append(port)

    ports = security_rule.get('destination_port_ranges')
    if ports is not None:
        all_ports.extend(ports)

    destination_ports = []
    for port in all_ports:
        if port == '*':
            destination_ports.append('0-65535')
        else:
            destination_ports.append(port)

    return destination_ports


def _get_normalized_rdbms_record(rdbms_record):
    """Normalize records of type `rdbms`.

    Arguments:
        rdbms_record (dict): RDBMS record generated by this plugin.

    Yields:
        dict: A normalized rdbms record.

    """
    ssl_enforcement = rdbms_record.get('raw', {}).get('ssl_enforcement')
    ssl_connection_enabled = (ssl_enforcement == 'Enabled')
    normalized_rdbms_record = {
        'raw': rdbms_record.get('raw', {}),
        'ext': util.merge_dicts(rdbms_record.get('ext'), {
            'reference': rdbms_record.get('raw', {}).get('id'),
        }),
        'com': util.merge_dicts(rdbms_record.get('com'), {
            'reference': rdbms_record.get('raw', {}).get('id'),
            'tls_enforced': ssl_connection_enabled,
        }),

    }
    yield normalized_rdbms_record
