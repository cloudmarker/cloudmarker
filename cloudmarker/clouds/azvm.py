"""Microsoft Azure virtual machine plugin to read Azure virtual machine data.

This module defines the :class:`AzVM` class that retrieves virtula machine data
from Microsoft Azure.
"""


import logging

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.resource import SubscriptionClient
from msrestazure import tools
from msrestazure.azure_exceptions import CloudError

from cloudmarker import util

_log = logging.getLogger(__name__)


class AzVM:
    """Azure Virtual Machine plugin."""

    def __init__(self, tenant, client, secret, _max_subs=0, _max_recs=0):
        """Create an instance of :class:`AzVM` plugin.

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
            _max_recs (int): Maximum number of virtual machines records
                to fetch for each subscription.
        """
        self._credentials = ServicePrincipalCredentials(
            tenant=tenant,
            client_id=client,
            secret=secret,
        )
        self._max_subs = _max_subs
        self._max_recs = _max_recs

    def read(self):
        """Return an Azure virtual machine record.

        Yields:
            dict: An Azure virtual machine record.

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

            yield from _get_record(compute_client, subscription_id,
                                   self._max_recs)

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
        up tasks associated with the :class:`AzVM` plugin. This
        may change in future.
        """


def _get_record(compute_client, subscription_id, max_recs):
    """Get virtual machine records with instance view details.

    Arguments:
        compute_client (ComputeManagementClient): Compute management client.
        subscription_id (str): Subscription ID.
        max_recs (int): Maximum number of records to fetch.

    Yields:
        dict: An Azure virtual machine record with instance view details.

    """
    try:
        virtual_machines_iter = compute_client.virtual_machines.list_all()

        for vm_index, vm in enumerate(virtual_machines_iter):
            rg_name = tools.parse_resource_id(vm.id)['resource_group']
            vm_iv = compute_client.virtual_machines.instance_view(rg_name,
                                                                  vm.name)
            yield from _process_vm_instance_view(vm, vm_iv,
                                                 vm_index, subscription_id)

            # Break after pulling data for self._max_recs number of
            # VMs for a subscriber. Note that if self._max_recs is 0 or
            # less, then the following condition never evaluates to True.
            if vm_index + 1 == max_recs:
                _log.info('Ending records fetch for subscription due '
                          'to _max_recs: %d; subscription_id: %s; ',
                          max_recs, subscription_id)
                break
    except CloudError as e:
        _log.error('Failed to fetch details for vm_instance_view; '
                   'subscription_id: %s; error: %s: %s',
                   subscription_id, type(e).__name__, e)


def _process_vm_instance_view(vm, vm_iv, vm_index, subscription_id):
    """Process virtual machine record and yeild them.

    Arguments:
        vm (VirtualMachine): Virtual Machine Descriptor
        vm_iv (VirtualMachineInstanceView): Virtual Machine Instance view
        subscription_id (str): Subscription ID.

    Yields:
        dict: An Azure record of type ``vm_instance_view``.

    """
    raw_record = vm.as_dict()
    raw_record['instance_view'] = vm_iv.as_dict()
    record = {
        'raw': raw_record,
        'ext': {
            'cloud_type': 'azure',
            'record_type': 'vm_instance_view',
            'subscription_id': subscription_id,
        },
        'com': {
            'cloud_type': 'azure',
            'record_type': 'compute',
            'reference': raw_record.get('id')
        }
    }
    record['ext'] = util.merge_dicts(
        record['ext'],
        _get_normalized_vm_statuses(vm_iv),
        _get_normalized_vm_disk_encryption_status(vm, vm_iv)
        )
    _log.info('Found vm_instance_view #%d; subscription_id: %s; name: %s',
              vm_index, subscription_id, record['raw'].get('name'))
    yield record


def _get_normalized_vm_statuses(vm_iv):
    """Iterate over a list of virtual machine statuses and normalize them.

    Arguments:
        vm_iv (VirtualMachineInstanceView): Virtual Machine Instance View

    Returns:
        dict: Normalized virtual machine statuses

    """
    normalized_statuses = {}
    for s in vm_iv.statuses:
        if s.code.startswith('PowerState/'):
            code_elements = s.code.split('/', 1)
            normalized_statuses['power_state'] = \
                code_elements[1].lower()
    return normalized_statuses


def _get_normalized_vm_disk_encryption_status(vm, vm_iv):
    """Iterate over a list of virtual machine disks normalize them.

    Arguments:
        vm (VirtualMachine): Virtual Machine
        vm_iv (VirtualMachineInstanceView): Virtual Machine Instance View

    Returns:
        dict: Normalized virtual machine disk encryption statuses

    """
    os_disk_name = vm.storage_profile.os_disk.name
    disk_enc_statuses = {}
    for disk in vm_iv.disks:
        if disk.name == os_disk_name:
            if disk.encryption_settings is None:
                disk_enc_statuses['os_disk_encrypted'] = False
            else:
                disk_enc_statuses['os_disk_encrypted'] = \
                    disk.encryption_settings[0].enabled
        else:
            if disk_enc_statuses.get('all_data_disks_encrypted', True):
                if disk.encryption_settings is None:
                    disk_enc_statuses['all_data_disks_encrypted'] = False
                else:
                    disk_enc_statuses['all_data_disks_encrypted'] = \
                        disk.encryption_settings[0].enabled
    return disk_enc_statuses
