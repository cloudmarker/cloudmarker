"""Microsoft Azure virtual machine plugin to read Azure virtual machine data.

This module defines the :class:`AzVM` class that retrieves virtula machine data
from Microsoft Azure.
"""


import logging

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.resource import SubscriptionClient
from msrestazure import tools

from cloudmarker import ioworkers, util

_log = logging.getLogger(__name__)


class AzVM:
    """Azure Virtual Machine plugin."""

    def __init__(self, tenant, client, secret, processes=4, threads=30,
                 _max_subs=0, _max_recs=0):
        """Create an instance of :class:`AzVM` plugin.

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
            _max_recs (int): Maximum number of virtual machines records
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
        """Return an Azure virtual machine record.

        Yields:
            dict: An Azure virtual machine record.

        """
        yield from ioworkers.run(self._get_tenant_vms,
                                 self._get_vm_instance_views,
                                 self._processes, self._threads,
                                 __name__)

    def _get_tenant_vms(self):
        """Get VMs from all subscriptions in a tenant.

        The yielded tuples when unpacked would become arguments for
        :meth:`_get_vm_instance_views`. Each such tuple represents a
        single unit of work that :meth:`_get_vm_instance_views` can work
        on independently in its own worker thread.

        Yields:
            tuple: A tuple which when unpacked forms valid arguments for
                :meth:`_get_vm_instance_views`.

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

                yield from self._get_subscription_vms(sub_index, sub)
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

    def _get_subscription_vms(self, sub_index, sub):
        """Get VMs from a single subscrption.

        Yields:
            tuple: A tuple which when unpacked forms valid arguments for
                :meth:`_get_vm_instance_views`.

        """
        try:
            tenant = self._tenant
            creds = self._credentials
            sub_id = sub.get('subscription_id')

            compute_client = ComputeManagementClient(creds, sub_id)
            vm_list = compute_client.virtual_machines.list_all()

            for vm_index, vm in enumerate(vm_list):
                vm = vm.as_dict()

                _log.info('Found VM #%d: %s; %s',
                          vm_index, vm.get('name'),
                          util.outline_az_sub(sub_index, sub, tenant))

                # Each VM is a unit of work.
                yield (vm_index, vm, sub_index, sub)

                # Break after pulling data for self._max_recs number
                # of VMs for a subscriber. Note that if
                # self._max_recs is 0 or less, then the following
                # condition never evaluates to True.
                if vm_index + 1 == self._max_recs:
                    _log.info('Stopping vm_instance_view fetch due '
                              'to _max_recs: %d; %s', self._max_recs,
                              util.outline_az_sub(sub_index, sub, tenant))
                    break
        except Exception as e:
            _log.error('Failed to fetch VMs; %s; error: %s: %s',
                       util.outline_az_sub(sub_index, sub, tenant),
                       type(e).__name__, e)

    def _get_vm_instance_views(self, vm_index, vm, sub_index, sub):
        """Get virtual machine records with instance view details.

        Arguments:
            vm_index (int): Virtual machine index (for logging only).
            vm (dict): Raw virtual machine record.
            sub_index (int): Subscription index (for logging only).
            sub (Subscription): Azure subscription object.

        Yields:
            dict: An Azure virtual machine record with instance view details.

        """
        vm_name = vm.get('name')
        _log.info('Working on VM #%d: %s; %s', vm_index, vm_name,
                  util.outline_az_sub(sub_index, sub, self._tenant))
        try:
            creds = self._credentials
            sub_id = sub.get('subscription_id')
            compute_client = ComputeManagementClient(creds, sub_id)
            vm_id = vm.get('id')
            rg_name = tools.parse_resource_id(vm_id)['resource_group']
            vm_iv = compute_client.virtual_machines.instance_view(rg_name,
                                                                  vm_name)
            vm_iv = vm_iv.as_dict()
            yield _process_vm_instance_view(vm_index, vm, vm_iv,
                                            sub_index, sub, self._tenant)
        except Exception as e:
            _log.error('Failed to fetch vm_instance_view for VM #%d: '
                       '%s; %s; error: %s: %s', vm_index, vm_name,
                       util.outline_az_sub(sub_index, sub, self._tenant),
                       type(e).__name__, e)

    def done(self):
        """Log a message that this plugin is done."""
        _log.info('Done; tenant: %s; processes: %s; threads: %s',
                  self._tenant, self._processes, self._threads)


def _process_vm_instance_view(vm_index, vm, vm_iv,
                              sub_index, sub, tenant):
    """Process virtual machine record and yeild them.

    Arguments:
        vm_index (int): Virtual machine index (for logging only).
        vm (dict): Raw virtual machine record.
        vm_iv (dict): Raw virtual machine instance view record.
        sub_index (int): Subscription index (for logging only).
        sub (Subscription): Azure subscription object.
        tenant (str): Azure tenant ID.

    Yields:
        dict: An Azure record of type ``vm_instance_view``.

    """
    vm['instance_view'] = vm_iv
    record = {
        'raw': vm,
        'ext': {
            'cloud_type': 'azure',
            'record_type': 'vm_instance_view',
            'subscription_id': sub.get('subscription_id'),
            'subscription_name': sub.get('display_name'),
            'subscription_state': sub.get('state'),
        },
        'com': {
            'cloud_type': 'azure',
            'record_type': 'compute',
            'reference': vm.get('id')
        }
    }
    record['ext'] = util.merge_dicts(
        record['ext'],
        _get_normalized_vm_statuses(vm_iv),
        _get_normalized_vm_disk_encryption_status(vm, vm_iv),
        _get_vm_extension_list(vm_iv)
        )
    _log.info('Found vm_instance_view #%d: %s; %s',
              vm_index, vm.get('name'),
              util.outline_az_sub(sub_index, sub, tenant))
    return record


def _get_normalized_vm_statuses(vm_iv):
    """Iterate over a list of virtual machine statuses and normalize them.

    Arguments:
        vm_iv (dict): Raw virtual machine instance view record.

    Returns:
        dict: Normalized virtual machine statuses

    """
    normalized_statuses = {}
    for s in vm_iv.get('statuses', []):
        code = s.get('code', '')
        if code.startswith('PowerState/'):
            code_elements = code.split('/', 1)
            normalized_statuses['power_state'] = code_elements[1].lower()
    return normalized_statuses


def _get_vm_extension_list(vm_iv):
    """Iterate over a list of virtual machine extensions.

    Arguments:
        vm_iv (dict): Raw virtual machine instance view record.

    Returns:
        dict: List of names of installed extensions

    """
    extensions = {}
    extension_list = []
    for e in vm_iv.get('extensions', []):
        extension_list.append(e['name'])
    extensions['extensions'] = extension_list
    return extensions


def _get_normalized_vm_disk_encryption_status(vm, vm_iv):
    """Iterate over a list of virtual machine disks normalize them.

    Arguments:
        vm (dict): Raw virtual machine record.
        vm_iv (dict): Raw virtual machine instance view record.

    Returns:
        dict: Normalized virtual machine disk encryption statuses

    """
    os_disk_name = vm.get('storage_profile', {}).get('os_disk', {}).get('name')
    disk_enc_statuses = {}
    for disk in vm_iv.get('disks', []):
        disk_name = disk.get('name')
        disk_encryption_settings = disk.get('encryption_settings')
        if disk_name == os_disk_name:
            if disk_encryption_settings is None:
                disk_enc_statuses['os_disk_encrypted'] = False
            else:
                disk_enc_statuses['os_disk_encrypted'] = \
                    disk_encryption_settings[0].get('enabled')
        else:
            if disk_enc_statuses.get('all_data_disks_encrypted', True):
                if disk_encryption_settings is None:
                    disk_enc_statuses['all_data_disks_encrypted'] = False
                else:
                    disk_enc_statuses['all_data_disks_encrypted'] = \
                        disk_encryption_settings[0].get('enabled')
    return disk_enc_statuses
