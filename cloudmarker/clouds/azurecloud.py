"""Microsoft Azure cloud plugin to read Azure infrastructure data.

This module defines the :class:`AzureCloud` class that retrieves data
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

_log = logging.getLogger(__name__)


class AzureCloud:
    """Azure cloud plugin."""

    def __init__(self, tenant, client, secret, _max_subs=0):
        """Create an instance of :class:`AzureCloud` plugin.

        Arguments:
            tenant (str): Azure subscription tenant ID.
            client (str): Azure service principal application ID.
            secret (str): Azure service principal password.
            _max_subs (int): Maximum number of subscribers to fetch
                data for if the value is greater than 0.

                Note: The ``_max_subs`` argument must be used only in
                the development-test-debug phase. It must not be used
                in production environment. This is why we use the
                convention of beginning its name with an underscore.
        """
        self._credentials = ServicePrincipalCredentials(
            tenant=tenant,
            client_id=client,
            secret=secret,
        )
        self._max_subs = _max_subs

    def read(self):
        """Return an Azure cloud infrastructure configuration document.

        Yields:
            dict: A document of the type ``record_type``.

        """
        # pylint: disable=R0914

        subscription_client = SubscriptionClient(self._credentials)

        for i, sub in enumerate(subscription_client.subscriptions.list()):
            sub_id = str(sub.subscription_id)
            _log.info('Found subscriber #%d; sub_id: %s; display_name: %s',
                      i, sub_id, sub.display_name)

            # Initialize Azure clients for the current subscriber.
            creds = self._credentials
            compute_client = ComputeManagementClient(creds, sub_id)
            network_client = NetworkManagementClient(creds, sub_id)
            storage_client = StorageManagementClient(creds, sub_id)
            resource_client = ResourceManagementClient(creds, sub_id)

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
            for doc in itertools.chain(
                    _get_doc(vm_list, 'virtual_machine', sub_id),
                    _get_doc(app_gw_list, 'app_gateway', sub_id),
                    _get_doc(lb_iter, 'lb', sub_id),
                    _get_doc(nic_list, 'nic', sub_id),
                    _get_doc(nsg_list, 'nsg', sub_id),
                    _get_doc(pubip_list, 'public_ip', sub_id),
                    _get_doc(storage_account_list, 'storage_account', sub_id),
                    _get_doc(resource_group_list, 'resource_group', sub_id),
                    _get_doc(resource_list, 'resource', sub_id),
            ):
                yield doc

            # Break after pulling data for self._max_subs number of
            # subscribers. Note that if self._max_subs is 0 or less,
            # then the following condition never evaluates to True.
            if i + 1 == self._max_subs:
                _log.info('Exiting read due to _max_subs: %d',
                          self._max_subs)
                break

    def done(self):
        """Perform clean up tasks.

        Currently, this method does nothing because there are no clean
        up tasks associated with the :class:`AzureCloud` plugin. This
        may change in future.
        """


def _get_doc(iterator, record_type, sub_id):
    """Process a list of :class:`msrest.serialization.Model` objects.

    Arguments:
        iterator: An iterator like instance of
            :class:`msrest.serialization.Model` objects.
        record_type (str): Type of the document.
        sub_id (str): Subscription ID.

    Yields:
        dict: A document of type ``record_type``.

    """
    try:
        for i, v in enumerate(iterator):
            doc = v.as_dict()
            doc['record_type'] = record_type
            doc['sub_id'] = sub_id

            _log.info('Found document %s #%d; sub_id: %s; name: %s',
                      record_type, i, sub_id, doc['name'])

            yield doc
    except CloudError as e:
        _log.error('Failed to fetch details for %s; sub_id: %s; error: %s: %s',
                   record_type, sub_id, type(e).__name__, e)
