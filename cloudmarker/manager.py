#!/usr/bin/env python


"""Manager of worker processes.

This module invokes the worker processes that perform the cloud security
monitoring tasks.
"""


from cloudmarker import util


def main():
    """Run the framework."""
    args = util.parse_cli()
    config = util.load_config(args.config)
    audits = _create_audit_plugins(config)
    _run_audits(audits)


def _create_audit_plugins(config):
    """Read configuration and construct all plugins.

    Arguments:
        config (dict): Framework configuration

    Returns:
        list: A list of tuples. Each tuple is of the format
            (cloud_plugin, store_plugins, check_plugins, alert_plugins) where
            store_plugins, check_plugins, and alert_plugins are lists of
            plugins of respective types.

    """
    audits = []

    for audit_name in config['run']:
        for cloud_name in config['audits'][audit_name]['clouds']:

            cloud_plugin = util.load_plugin(config['clouds'][cloud_name])

            store_plugins = [
                util.load_plugin(config['stores'][store_name])
                for store_name in config['audits'][audit_name]['stores']
            ]

            check_plugins = [
                util.load_plugin(config['checks'][store_name])
                for store_name in config['audits'][audit_name]['checks']
            ]

            alert_plugins = [
                util.load_plugin(config['alerts'][store_name])
                for store_name in config['audits'][audit_name]['alerts']
            ]

            audits.append((cloud_plugin, store_plugins, check_plugins,
                           alert_plugins))

    return audits


def _run_audits(audits):
    """Run all plugins to perform auditing.

    Arguments:
        audits (list): A list returned by _create_audit_plugins.

    """
    # For each cloud configured for auditing ...
    for cloud, stores, checks, alerts in audits:

        # For each cloud record read from the cloud ...
        for cloud_record in cloud.read():

            # Write the record in each configured store.
            for store in stores:
                store.write(cloud_record)

            # Also feed the record to each checker.
            for check in checks:

                # For each anomaly record obtained from checker ...
                for check_record in check.eval(cloud_record):

                    # Send each check record as an alert.
                    for alert in alerts:
                        alert.write(check_record)

        # Tell each plugin that there is nothing more to do, so that
        # they perform any final cleanup tasks.
        cloud.done()

        for check in checks:
            check.done()

        for store in stores:
            store.done()

        for alert in alerts:
            alert.done()
