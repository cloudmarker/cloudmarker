"""Microsoft Azure disk plugin to read Azure disk data.

This module defines the :class:`AzDisk` class that retrieves disk
from Microsoft Azure.
"""


import logging

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.resource import SubscriptionClient
from msrestazure import tools

from cloudmarker import ioworkers, util

_log = logging.getLogger(__name__)


class AzDisk:
    """Azure disk plugin."""

    def __init__(self, tenant, client, secret, processes=4, threads=30,
                 _max_subs=0, _max_recs=0):
        """Create an instance of :class:`AzDisk` plugin.

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
        """Return an Azure disk record.

        Yields:
            dict: An Azure disk record.

        """
        yield from ioworkers.run(self._get_tenant_disks,
                                 self._get_disk_details,
                                 self._processes, self._threads,
                                 __name__)

    def _get_tenant_disks(self):
        """Get disk from all subscriptions in a tenant.

        The yielded tuples when unpacked would become arguments for
        :meth:`_get_disk_details`. Each such tuple represents a
        single unit of work that :meth:`_get_disk_details` can
        work on independently in its own worker thread.

        Yields:
            tuple: A tuple which when unpacked forms valid arguments for
                :meth:`_get_disk_details`.

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

                yield from self._get_subscription_disks(sub_index, sub)
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

    def _get_subscription_disks(self, sub_index, sub):
        """Get disks from a single subscrption.

        Arguments:
            sub_index (int): Subscription index (for logging only).
            sub (Subscription): Azure subscription object.

        Yields:
            tuple: A tuple which when unpacked forms valid arguments for
                :meth:`_get_disk_details`.

        """
        try:
            tenant = self._tenant
            creds = self._credentials
            sub_id = sub.get('subscription_id')
            compute_client = ComputeManagementClient(creds, sub_id)
            disk_list = compute_client.disks.list()

            for disk_index, disk in enumerate(disk_list):
                disk = disk.as_dict()
                disk_id = disk.get('id')
                disk_name = disk.get('name')
                _log.info('Found disk #%d: %s; %s',
                          disk_index, disk_name,
                          util.outline_az_sub(sub_index, sub, tenant))
                rg_name = \
                    tools.parse_resource_id(disk_id)['resource_group']
                yield (disk_index, disk_name, rg_name, sub_index, sub)

                # Break after pulling data for self._max_recs number
                # of disks for a subscriber. Note that if
                # self._max_recs is 0 or less, then the following
                # condition never evaluates to True.
                if disk_index + 1 == self._max_recs:
                    _log.info('Stopping disk fetch due '
                              'to _max_recs: %d; %s', self._max_recs,
                              util.outline_az_sub(sub_index, sub,
                                                  self._tenant))
                    break
        except Exception as e:
            _log.error('Failed to fetch disks; %s; error: %s: %s',
                       util.outline_az_sub(sub_index, sub, tenant),
                       type(e).__name__, e)

    def _get_disk_details(self, disk_index, disk_name, rg_name,
                          sub_index, sub):
        """Get details of disk.

        Arguments:
            sub_index (int): Subscription index (for logging only).
            sub (Subscription): Azure subscription object.
            rg_name (str): Resource group name.
            disk_index (int): Disk index (for logging only).
            disk_name (str): Name of the disk.

        Yields:
            dict: An Azure disk record.

        """
        _log.info('Working on disk #%d: %s; %s', disk_index,
                  disk_name, util.outline_az_sub(disk_index, sub,
                                                 self._tenant))
        try:
            sub_id = sub.get('subscription_id')
            creds = self._credentials
            compute_client = ComputeManagementClient(creds, sub_id)
            disk = compute_client.disks.get(rg_name, disk_name)
            disk = disk.as_dict()
            yield _process_disk_details(sub, disk)
        except Exception as e:
            _log.error('Failed to fetch disk details #%d: '
                       '%s; %s; error: %s: %s', disk_index, disk_name,
                       util.outline_az_sub(sub_index, sub, self._tenant),
                       type(e).__name__, e)

    def done(self):
        """Log a message that this plugin is done."""
        _log.info('Done; tenant: %s; processes: %s; threads: %s',
                  self._tenant, self._processes, self._threads)


def _process_disk_details(sub, disk):
    """Process disk record and yield them.

    Arguments:
        sub (Subscription): Azure subscription object.
        disk (dict): Raw disk record.

    Yields:
        dict: An Azure record of type ``disk``.

    """
    disk_type = 'unattached'
    if 'managed_by' in disk:
        if disk.get('managed_by'):
            disk_type = 'attached'

    record = {
        'raw': disk,
        'ext': {
            'cloud_type': 'azure',
            'record_type': 'disk',
            'disk_type': disk_type,
            'subscription_id': sub.get('subscription_id'),
            'subscription_name': sub.get('display_name'),
            'subscription_state': sub.get('state'),
        },
        'com': {
            'cloud_type': 'azure',
            'record_type': 'disk',
            'reference': disk.get('id')
        }
    }
    return record
