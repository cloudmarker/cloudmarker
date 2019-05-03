"""Microsoft Azure cloud plugin to read Azure infrastructure data.

This module defines the :class:`AzCloud` class that retrieves data
from Microsoft Azure.
"""


import itertools
import logging

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient, SubscriptionClient
from azure.mgmt.storage import StorageManagementClient
from msrestazure.azure_exceptions import CloudError

from cloudmarker import util

_log = logging.getLogger(__name__)


class AzCloud:
    """Azure cloud plugin."""

    def __init__(self, tenant, client, secret, _max_subs=0, _max_recs=0):
        """Create an instance of :class:`AzCloud` plugin.

         Note: The ``_max_subs`` and ``_max_recs`` arguments should be
         used only in the development-test-debug phase. They should not
         be used in production environment. This is why we use the
         convention of beginning their names with underscore.

        Arguments:
            tenant (str): Azure subscription tenant ID.
            client (str): Azure service principal application ID.
            secret (str): Azure service principal password.
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
        self._max_subs = _max_subs
        self._max_recs = _max_recs

    def read(self):
        """Return an Azure cloud infrastructure configuration record.

        Yields:
            dict: An Azure cloud infrastructure configuration record.

        """
        # pylint: disable=R0914

        subscription_client = SubscriptionClient(self._credentials)

        for i, sub in enumerate(subscription_client.subscriptions.list()):
            subscription_id = str(sub.subscription_id)
            _log.info('Found subscription #%d; subscription_id: %s; '
                      'display_name: %s',
                      i, subscription_id, sub.display_name)

            # Initialize Azure clients for the current subscription.
            creds = self._credentials
            compute_client = ComputeManagementClient(creds, subscription_id)
            network_client = NetworkManagementClient(creds, subscription_id)
            storage_client = StorageManagementClient(creds, subscription_id)
            resource_client = ResourceManagementClient(creds, subscription_id)

            # Get iterators for each type of data.
            vm_list = compute_client.virtual_machines.list_all()
            app_gw_list = network_client.application_gateways.list_all()
            lb_iter = network_client.load_balancers.list_all()
            nic_list = network_client.network_interfaces.list_all()
            nsg_list = network_client.network_security_groups.list_all()
            pubip_list = network_client.public_ip_addresses.list_all()
            storage_account_list = storage_client.storage_accounts.list()
            resource_group_list = resource_client.resource_groups.list()
            resource_list = resource_client.resources.list()

            # Retrieve data using each iterator.
            for record in itertools.chain(
                    _get_record(vm_list, 'virtual_machine',
                                subscription_id, self._max_recs),

                    _get_record(app_gw_list, 'app_gateway',
                                subscription_id, self._max_recs),

                    _get_record(lb_iter, 'lb',
                                subscription_id, self._max_recs),

                    _get_record(nic_list, 'nic',
                                subscription_id, self._max_recs),

                    _get_record(nsg_list, 'nsg',
                                subscription_id, self._max_recs),

                    _get_record(pubip_list, 'public_ip',
                                subscription_id, self._max_recs),

                    _get_record(storage_account_list, 'storage_account',
                                subscription_id, self._max_recs),

                    _get_record(resource_group_list, 'resource_group',
                                subscription_id, self._max_recs),

                    _get_record(resource_list, 'resource',
                                subscription_id, self._max_recs),
            ):
                yield record

            # Break after pulling data for self._max_subs number of
            # subscriptions. Note that if self._max_subs is 0 or less,
            # then the following condition never evaluates to True.
            if i + 1 == self._max_subs:
                _log.info('Ending subscriptions fetch due to '
                          '_max_subs: %d', self._max_subs)
                break

    def done(self):
        """Perform clean up tasks.

        Currently, this method does nothing because there are no clean
        up tasks associated with the :class:`AzCloud` plugin. This
        may change in future.
        """


def _get_record(iterator, azure_record_type, subscription_id, _max_recs):
    """Process a list of :class:`msrest.serialization.Model` objects.

    Arguments:
        iterator: An iterator like instance of
            :class:`msrest.serialization.Model` objects.
        azure_record_type (str): Type of record as per Azure vocabulary.
        subscription_id (str): Subscription ID.
        _max_recs (int): Maximum number of records to fetch.

    Yields:
        dict: An Azure record of type ``record_type``.

    """
    # Dictionary to map Azure record types to common record types.
    record_type_map = {
        'virtual_machine': 'compute',
    }

    try:
        for i, v in enumerate(iterator):
            raw_record = v.as_dict()
            record = {
                'raw': raw_record,
                'ext': {
                    'cloud_type': 'azure',
                    'record_type': azure_record_type,
                    'subscription_id': subscription_id,
                },
                'com': {
                    'cloud_type': 'azure',
                    'record_type': record_type_map.get(azure_record_type)
                }
            }

            _log.info('Found %s #%d; subscription_id: %s; name: %s',
                      azure_record_type, i, subscription_id,
                      record['raw'].get('name'))

            yield record

            # For every security rule found in an NSG, generate a
            # separate security rule (firewall rule) record to maintain
            # parity with separate records for separate firewall rules
            # in GCP.
            if azure_record_type == 'nsg':
                yield from _get_normalized_firewall_rules(record,
                                                          subscription_id)

            if i + 1 == _max_recs:
                _log.info('Ending records fetch for subscription due '
                          'to _max_recs: %d; subscription_id: %s; '
                          'record_type: %s', _max_recs,
                          subscription_id, azure_record_type)
                break

    except CloudError as e:
        _log.error('Failed to fetch details for %s; subscription_id: %s; '
                   'error: %s: %s',
                   azure_record_type, subscription_id, type(e).__name__, e)


def _get_normalized_firewall_rules(nsg_record, subscription_id):
    """Split a network security group (NSG) into multiple firewall rules.

    An Azure NSG record contains a top-level key named
    ``security_rules`` whose value is a list of security rules.

    In order to make it easier to write event plugins to detect security
    issues in an NSG, we generate a new firewall rule record for each
    security rule found in the NSG.

    Arguments:
        nsg_record (dict): NSG record generated by this plugin.
        subscription_id (str): Subscription ID (for logging purpose only).

    Yields:
        dict: A normalized firewall rule record with ``com`` bucket
            populated with firewall rule properties in common notation.

    """
    security_rules = nsg_record.get('raw', {}).get('security_rules')
    nsg_name = nsg_record.get('raw', {}).get('name')

    if security_rules is None:
        _log.warning('Found NSG without security_rules; name: %s', nsg_name)
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

        _log.info('Found security_rule #%d; subscription_id: %s; name: %s',
                  i, subscription_id, security_rule.get('name'))
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
