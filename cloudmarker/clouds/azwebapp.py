"""Microsoft Azure web apps plugin to read Azure web app data.

This module defines the :class:`AzWebApp` class that retrieves web apps
data from Microsoft Azure.
"""


import logging

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.web import WebSiteManagementClient
from msrestazure import tools

from cloudmarker import ioworkers, util

_log = logging.getLogger(__name__)


class AzWebApp:
    """Azure web app plugin."""

    def __init__(self, tenant, client, secret, processes=4,
                 threads=30, _max_subs=0, _max_recs=0):
        """Create an instance of :class:`AzWebApp` plugin.

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
            _max_recs (int): Maximum number of web apps records
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
        """Return an Azure web app record.

        Yields:
            dict: An Azure web app record.

        """
        yield from ioworkers.run(self._get_tenant_web_apps,
                                 self. _get_web_app_configs,
                                 self._processes, self._threads,
                                 __name__)

    def _get_tenant_web_apps(self):
        """Get web apps from all subscriptions in a tenant.

        The yielded tuples when unpacked would become arguments for
        :meth:` _get_web_app_configs`. Each such tuple represents a
        single unit of work that :meth:` _get_web_app_configs` can work
        on independently in its own worker thread.

        Yields:
            tuple: A tuple which when unpacked forms valid arguments for
                :meth:` _get_web_app_configs`.

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
                yield from self._get_subscription_apps(sub_index, sub)
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

    def _get_subscription_apps(self, sub_index, sub):
        """Get web apps from a single subscrption.

        Yields:
            tuple: A tuple which when unpacked forms valid arguments for
                :meth:` _get_web_app_configs`.

        """
        try:
            tenant = self._tenant
            creds = self._credentials
            sub_id = sub.get('subscription_id')

            web_client = WebSiteManagementClient(creds, sub_id)
            web_list = web_client.web_apps.list()

            for app_index, app in enumerate(web_list):
                app = app.as_dict()

                _log.info('Found web app #%d: %s; %s',
                          app_index, app.get('name'),
                          util.outline_az_sub(sub_index, sub, tenant))

                # Each app is a unit of work.
                yield (app_index, app, sub_index, sub)

                # Break after pulling data for self._max_recs number
                # of web apps for a subscriber. Note that if
                # self._max_recs is 0 or less, then the following
                # condition never evaluates to True.
                if app_index + 1 == self._max_recs:
                    _log.info('Stopping web app fetch due '
                              'to _max_recs: %d; %s', self._max_recs,
                              util.outline_az_sub(sub_index, sub, tenant))
                    break
        except Exception as e:
            _log.error('Failed to fetch web apps; %s; error: %s: %s',
                       util.outline_az_sub(sub_index, sub, tenant),
                       type(e).__name__, e)

    def _get_web_app_configs(self, app_index, app, sub_index, sub):
        """Get web app records with config details.

        Arguments:
            app_index (int): Web app index (for logging only).
            app (dict): Raw web app record.
            sub_index (int): Subscription index (for logging only).
            sub (Subscription): Azure subscription object.

        Yields:
            dict: An Azure web app record with config details.

        """
        app_name = app.get('name')
        _log.info('Working on web app #%d: %s; %s', app_index, app_name,
                  util.outline_az_sub(sub_index, sub, self._tenant))
        try:
            creds = self._credentials
            sub_id = sub.get('subscription_id')
            web_client = WebSiteManagementClient(creds, sub_id)
            app_id = app.get('id')
            rg_name = tools.parse_resource_id(app_id)['resource_group']
            app_config = web_client.web_apps.get_configuration(rg_name,
                                                               app_name)
            app_config = app_config.as_dict()
            yield _process_app_config(app_index, app, app_config,
                                      sub_index, sub, self._tenant)
        except Exception as e:
            _log.error('Failed to fetch app_config for web app #%d: '
                       '%s; %s; error: %s: %s', app_index, app_name,
                       util.outline_az_sub(sub_index, sub, self._tenant),
                       type(e).__name__, e)

    def done(self):
        """Log a message that this plugin is done."""
        _log.info('Done; tenant: %s; processes: %s; threads: %s',
                  self._tenant, self._processes, self._threads)


def _process_app_config(app_index, app, app_config,
                        sub_index, sub, tenant):
    """Process web app record and yield them.

    Arguments:
        app_index (int): Web app index (for logging only).
        app (dict): Raw web app record.
        app_config (dict): Raw web app config record.
        sub_index (int): Subscription index (for logging only).
        sub (Subscription): Azure subscription object.
        tenant (str): Azure tenant ID.

    Yields:
        dict: An Azure record of type ``web_app_config``.

    """
    app['config'] = app_config
    record = {
        'raw': app,
        'ext': {
            'cloud_type': 'azure',
            'record_type': 'web_app_config',
            'https_only': app.get('https_only'),
            'client_cert_enabled': app.get('client_cert_enabled'),
            'http20_enabled': app_config.get('http20_enabled'),
            'min_tls_version': app_config.get('min_tls_version'),
            'subscription_id': sub.get('subscription_id'),
            'subscription_name': sub.get('display_name'),
            'subscription_state': sub.get('state'),
        },
        'com': {
            'cloud_type': 'azure',
            'reference': app.get('id')
        }
    }
    _log.info('Found web_app_config #%d: %s; %s',
              app_index, app.get('name'),
              util.outline_az_sub(sub_index, sub, tenant))
    return record
