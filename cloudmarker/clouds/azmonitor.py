"""Microsoft Azure monitor plugin to read Azure monitoring data.

This module defines the :class:`AzMonitor` class that retrieves data
from Microsoft Azure.
"""


import logging

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.monitor import MonitorManagementClient
from azure.mgmt.resource import SubscriptionClient

from cloudmarker import ioworkers, util

_log = logging.getLogger(__name__)


class AzMonitor:
    """Azure monitor plugin."""

    def __init__(self, tenant, client, secret, processes=4,
                 threads=30, _max_subs=0, _max_recs=0):
        """Create an instance of :class:`AzMonitor` plugin.

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
        """Return an Azure monitor record.

        Yields:
            dict: An Azure monitor record.

        """
        yield from ioworkers.run(self._get_subscriptions,
                                 self._get_profiles,
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

            monitor_attributes = ('log_profile',)

            tenant = self._tenant
            for sub_index, sub in enumerate(sub_list):
                sub = sub.as_dict()
                _log.info('Found %s', util.outline_az_sub(sub_index,
                                                          sub, tenant))
                # Each record type for each subscription is a unit of
                # work that would be fed to _get_resources().
                for attribute_type in monitor_attributes:
                    if attribute_type == 'log_profile':
                        sub['locations'] = list()
                        locations = sub_client.subscriptions. \
                            list_locations(sub.get('subscription_id'))
                        for location in locations:
                            sub['locations'].append(location.as_dict()
                                                    .get('name'))
                    yield (attribute_type, sub_index, sub)

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

    def _get_profiles(self, attribute_type, sub_index, sub):
        """Return an Azure monitor record.

        Arguments:
            attribute_type (str): Attribute type name.
            sub_index (int): Subscription index (for logging only).
            sub (Subscription): Azure subscription object.

        Yields:
            dict: An Azure monitor record.

        """
        _log.info('Working on %s', util.outline_az_sub(sub_index, sub,
                                                       self._tenant))
        try:
            monitor_client = \
                MonitorManagementClient(self._credentials,
                                        sub.get('subscription_id'))
            iterator = \
                _get_attribute_iterator(attribute_type, monitor_client,
                                        sub, sub_index, self._tenant)
            yield from _get_record(iterator, attribute_type, self._max_recs,
                                   sub_index, sub, self._tenant)
        except Exception as e:
            _log.error('Failed to fetch details for %s; %s; error: %s: %s',
                       attribute_type,
                       util.outline_az_sub(sub_index, sub, self._tenant),
                       type(e).__name__, e)

    def done(self):
        """Log a message that this plugin is done."""
        _log.info('Done; tenant: %s; processes: %s; threads: %s',
                  self._tenant, self._processes, self._threads)


def _get_attribute_iterator(attribute_type, monitor_client,
                            sub, sub_index, tenant):
    """Return an appropriate iterator for ``attribute_type``.

    Arguments:
        attribute_type (str): Attribute type.
        monitor_client(MonitorManagementClient): Monitor client.
        credentials (ServicePrincipalCredentials): Credentials.
        sub_index (int): Subscription index (for logging only).
        sub (Subscription): Subscription object.
        tenant (str): Tenant ID (for logging only).

    Returns:
        msrest.paging.Paged: An Azure paging container for iterating
            over a list of Azure resource objects.

    """
    if attribute_type == 'log_profile':
        return monitor_client.log_profiles.list()

    # If control reaches here, there is a bug in this plugin. It means
    # there is a value in attributes variable in _get_subscriptions
    # that is not handled in the above if-statements.
    _log.warning('Unrecognized profile_type: %s; %s', attribute_type,
                 util.outline_az_sub(sub_index, sub, tenant))
    return None


def _get_record(iterator, attribute_type, max_recs,
                sub_index, sub, tenant):
    """Process a list of :class:`msrest.serialization.Model` objects.

    Arguments:
        iterator: An iterator like instance of
            :class:`msrest.serialization.Model` objects.
        attribute_type (str): Type of record as per Azure vocabulary.
        max_recs (int): Maximum number of records to fetch.
        sub_index (int): Subscription index (for logging only).
        sub (Subscription): Azure subscription model object.
        tenant (str): Azure tenant ID (for logging only).

    Yields:
        dict: An Azure record of type ``attribute_type``.

    """
    base_record = {
        'ext': {
            'cloud_type': 'azure',
            'record_type': attribute_type,
            'subscription_id': sub.get('subscription_id'),
            'subscription_name': sub.get('display_name'),
            'subscription_state': sub.get('state'),
        },
        'com': {
            'cloud_type': 'azure',
            'record_type': attribute_type,
        }
    }

    records_missing = True

    for i, v in enumerate(iterator):
        raw_record = v.as_dict()
        _log.info('Found %s #%d: %s; %s', attribute_type, i,
                  raw_record.get('name'),
                  util.outline_az_sub(sub_index, sub, tenant))
        retention_policy = raw_record.get('retention_policy')
        record = util.merge_dicts(base_record, {
            'raw': raw_record,
            'ext': {
                'cloud_type': 'azure',
                'record_type': attribute_type,
                'subscription_id': sub.get('subscription_id'),
                'subscription_name': sub.get('display_name'),
                'subscription_state': sub.get('state'),
                'retention_enabled': retention_policy.get('enabled'),
                'retention_days': retention_policy.get('days'),
            },
            'com': {
                'reference': raw_record.get('id'),
            }
        })
        if 'locations' in sub:
            record['ext']['subscription_locations'] = sub.get('locations')
        if attribute_type == 'log_profile':
            record['ext']['locations'] = raw_record.get('locations')

        # We have found at least one record, so we set this flag to False.
        records_missing = False

        yield record

        if i + 1 == max_recs:
            _log.info('Stopping %s fetch due to _max_recs: %d; %s',
                      attribute_type, max_recs,
                      util.outline_az_sub(sub_index, sub, tenant))
            break

    if records_missing:
        _log.info('Missing %s; %s', attribute_type,
                  util.outline_az_sub(sub_index, sub, tenant))

        record = util.merge_dicts(base_record, {
            'raw': None,
            'ext': {
                'record_type': attribute_type + '_missing',
            },
            'com': {
                'record_type': attribute_type + '_missing',
                'reference': sub.get('id'),
            }
        })
        yield record
