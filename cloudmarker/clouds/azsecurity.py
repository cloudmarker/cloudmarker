"""Microsoft Azure Security plugin to read Azure security center data.

This module defines the :class:`AzSecurity` class that retrieves security
center data from Microsoft Azure.
"""


import logging

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.security import SecurityCenter

from cloudmarker import ioworkers, util

_log = logging.getLogger(__name__)


class AzSecurity:
    """Azure Security plugin."""

    def __init__(self, tenant, client, secret, processes=4, threads=30,
                 _max_subs=0):
        """Create an instance of :class:`AzSEcurity` plugin.

         Note: The ``_max_subs`` argument should be used only in the
         development-test-debug phase. They should not be used in
         production environment. This is why we use the convention
         of beginning their names with underscore.

        Arguments:
            tenant (str): Azure subscription tenant ID.
            client (str): Azure service principal application ID.
            secret (str): Azure service principal password.
            processes (int): Number of worker processes to run.
            threads (int): Number of worker threads to run.
            _max_subs (int): Maximum number of subscriptions to fetch
                data for if the value is greater than 0.

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
        _log.info('Initialized; tenant: %s; processes: %s; threads: %s',
                  self._tenant, self._processes, self._threads)

    def read(self):
        """Return an Azure security center record.

        Yields:
            dict: An Azure security center record.

        """
        yield from ioworkers.run(self._get_tenant_asc,
                                 self._get_security_center,
                                 self._processes, self._threads,
                                 __name__)

    def _get_tenant_asc(self):
        """Get security center from all subscriptions in a tenant.

        The yielded tuples when unpacked would become arguments for
        :meth:`_get_subscription_asc`. Each such tuple represents a
        single unit of work that :meth:`_get_subscription_asc` can work
        on independently in its own worker thread.

        Yields:
            tuple: A tuple which when unpacked forms valid arguments for
                :meth:`_get_subscription_asc`.

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

                yield from self._get_subscription_asc(sub_index, sub)
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

    def _get_subscription_asc(self, sub_index, sub):
        """Get security center from a single subscrption.

        Yields:
            tuple: A tuple which when unpacked forms valid arguments for
                :meth:`_get_security_center`.

        """
        try:
            tenant = self._tenant
            creds = self._credentials
            sub_id = sub.get('subscription_id')
            asc_location = "centralus"
            security_center = SecurityCenter(creds, sub_id, asc_location)
            asc_locations = security_center.locations.list()
            for _, loc in enumerate(asc_locations):
                asc_location = loc.name
            yield (asc_location, sub_index, sub)
        except Exception as e:
            _log.error('Failed to fetch security center; %s; error: %s: %s',
                       util.outline_az_sub(sub_index, sub, tenant),
                       type(e).__name__, e)

    def _get_security_center(self, asc_location, sub_index, sub):
        """Get security center details.

        Arguments:
            asc_location (str): Location of the security center.
            sub_index (int): Subscription index (for logging only).
            sub (Subscription): Azure subscription object.

        Yields:
            dict: An Azure security center record with details of various
            components.

        """
        _log.info('Working on Az Security Center: %s; %s', asc_location,
                  util.outline_az_sub(sub_index, sub, self._tenant))
        try:
            creds = self._credentials
            sub_id = sub.get('subscription_id')
            security_center = SecurityCenter(creds, sub_id, asc_location)
            pricings = security_center.pricings.list().as_dict()['value']

            contacts_list = security_center.security_contacts.list()
            contacts = []
            for _, contact in enumerate(contacts_list):
                contacts.append(contact.as_dict())

            settings_list = security_center.settings.list()
            settings = []
            for _, setting in enumerate(settings_list):
                settings.append(setting.as_dict())

            auto_provisioning_settings_list = security_center. \
                auto_provisioning_settings.list()
            auto_provisioning_settings = []
            for _, ap_setting in enumerate(auto_provisioning_settings_list):
                auto_provisioning_settings.append(ap_setting.as_dict())

            jit_network_access_policies_list = security_center. \
                jit_network_access_policies.list()
            jit_network_access_policies = []
            for _, policy in enumerate(jit_network_access_policies_list):
                jit_network_access_policies.append(policy.as_dict())

            allowed_connections_list = security_center. \
                allowed_connections.list()
            allowed_connections = []
            for _, connection in enumerate(allowed_connections_list):
                allowed_connections.append(connection.as_dict())

            tasks_list = security_center.tasks.list()
            tasks = []
            for _, task in enumerate(tasks_list):
                tasks.append(task.as_dict())

            yield _process_asc(asc_location, contacts, pricings, settings,
                               auto_provisioning_settings,
                               jit_network_access_policies,
                               allowed_connections, tasks,
                               sub_index, sub, self._tenant)
        except Exception as e:
            _log.error('Failed to fetch security center details : '
                       '%s; error: %s: %s',
                       util.outline_az_sub(sub_index, sub, self._tenant),
                       type(e).__name__, e)

    def done(self):
        """Log a message that this plugin is done."""
        _log.info('Done; tenant: %s; processes: %s; threads: %s',
                  self._tenant, self._processes, self._threads)


def _process_asc(location, contacts, pricings, settings,
                 auto_provisioning_settings,
                 jit_network_access_policies, allowed_connections,
                 tasks, sub_index, sub, tenant):
    """Process security center components and yeild them.

    Arguments:
        location (str): Location of the security center.
        contacts (dict): Security contacts record.
        pricings (dict): Security pricings record.
        settings (dict): Security center settings record.
        auto_provisioning_settings (dict): Auto provisioning record.
        jit_network_access_policies (dict): JIT network access policy record.
        allowed_connections (dict): Allowed connections record.
        tasks (dict): Security center tasks record.
        sub_index (int): Subscription index (for logging only).
        sub (Subscription): Azure subscription object.
        tenant (str): Azure tenant ID.

    Yields:
        dict: An Azure record of type ``security_manager``.

    """
    security_center = {}
    security_center['pricings'] = pricings
    security_center['contacts'] = contacts
    security_center['settings'] = settings
    security_center['auto_provisioning_settings'] = \
        auto_provisioning_settings
    security_center['jit_network_access_policies'] = \
        jit_network_access_policies
    security_center['allowed_connections'] = \
        allowed_connections
    security_center['tasks'] = tasks
    record = {
        'raw': security_center,
        'ext': {
            'cloud_type': 'azure',
            'record_type': 'security_center',
            'subscription_id': sub.get('subscription_id'),
            'subscription_name': sub.get('display_name'),
            'subscription_state': sub.get('state'),
        },
        'com': {
            'cloud_type': 'azure',
            'record_type': 'security_manager',
        }
    }
    _log.info('Found security center : %s; %s',
              location,
              util.outline_az_sub(sub_index, sub, tenant))
    return record
