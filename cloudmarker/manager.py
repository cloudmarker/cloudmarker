#!/usr/bin/env python


"""Manager of worker subprocesses.

This module invokes the worker subprocesses that perform the cloud
security monitoring tasks. Each worker subprocess wraps around a cloud,
store, event, or alert plugin and executes the plugin in a separate
subprocess.
"""


import logging.config
import multiprocessing as mp
import time

import schedule

import cloudmarker
from cloudmarker import baseconfig, util, workers

# Define module-level logger.
_log = logging.getLogger(__name__)


def main():
    """Run the framework based on the schedule."""
    # Configure the logger as the first thing as per the base
    # configuration. We need this to be the first thing, so that
    # we can see the messages logged by util.load_config().
    logging.config.dictConfig(baseconfig.config_dict['logger'])
    _log.info('Cloudmarker %s', cloudmarker.__version__)

    # Parse the command line arguments and handle the options that can
    # be handled immediately.
    args = util.parse_cli()
    if args.print_base_config:
        print(baseconfig.config_yaml.strip())
        return

    # Now load user's configuration files.
    config = util.load_config(args.config)

    # Then configure the logger once again to honour any logger
    # configuration defined in the user's configuration files.
    logging.config.dictConfig(config['logger'])

    # Finally, run the audits, either right now or as per a schedule,
    # depending on the command line options.
    if args.now:
        _log.info('Starting job now')
        job(config)
    else:
        _log.info('Scheduled to run job everyday at %s', config['schedule'])
        schedule.every().day.at(config['schedule']).do(job, config)
        while True:
            schedule.run_pending()
            time.sleep(60)


def job(config):
    """Run the audits.

    Arguments:
        config (dict): Configuration dictionary.
    """
    # Create an audit object for each audit configured to be run.
    audits = []
    for audit_name in config['run']:
        audits.append(Audit(audit_name, config))

    # Start all audits.
    for audit in audits:
        audit.start()

    # Wait for all audits to terminate.
    for audit in audits:
        audit.join()


class Audit:
    """Audit manager.

    This class encapsulates a set of worker subprocesses and worker
    input queues for a single audit configuration.
    """

    def __init__(self, audit_name, config):
        """Create an instance of :class:`Audit` from configuration.

        A single audit definition (from a list of audit definitions
        under the ``audits`` key in the configuration) is instantiated.
        Each audit definition contains lists of cloud plugins, store
        plugins, event plugins, and alert plugins. These plugins are
        instantiated and multiprocessing queues are set up to take
        records from one plugin and feed them to another plugin as per
        the audit workflow.

        Arguments:
            audit_name (str): Key name for an audit configuration. This
                key is looked for in ``config['audits']``.
            config (dict): Configuration dictionary. This is the
                entire configuration dictionary that contains
                top-level keys named ``clouds``, ``stores``, ``events``,
                ``alerts``, ``audits``, ``run``, etc.
        """
        audit_config = config['audits'][audit_name]

        # We keep all workers in these lists.
        self._cloud_workers = []
        self._store_workers = []
        self._event_workers = []
        self._alert_workers = []

        # We keep all queues in these lists.
        self._store_queues = []
        self._event_queues = []
        self._alert_queues = []

        # Create alert workers and queues.
        for name in audit_config['alerts']:
            input_queue = mp.Queue()
            args = (
                audit_name + '-' + name,
                util.load_plugin(config['alerts'][name]),
                input_queue,
            )
            worker = mp.Process(target=workers.store_worker, args=args)
            self._alert_workers.append(worker)
            self._alert_queues.append(input_queue)

        # Create event_workers workers and queues.
        for name in audit_config['events']:
            input_queue = mp.Queue()
            args = (
                audit_name + '-' + name,
                util.load_plugin(config['events'][name]),
                input_queue,
                self._alert_queues,
            )
            worker = mp.Process(target=workers.event_worker, args=args)
            self._event_workers.append(worker)
            self._event_queues.append(input_queue)

        # Create store workers and queues.
        for name in audit_config['stores']:
            input_queue = mp.Queue()
            args = (
                audit_name + '-' + name,
                util.load_plugin(config['stores'][name]),
                input_queue,
            )
            worker = mp.Process(target=workers.store_worker, args=args)
            self._store_workers.append(worker)
            self._store_queues.append(input_queue)

        # Create cloud workers.
        for name in audit_config['clouds']:
            args = (
                audit_name + '-' + name,
                util.load_plugin(config['clouds'][name]),
                self._store_queues + self._event_queues
            )
            worker = mp.Process(target=workers.cloud_worker, args=args)
            self._cloud_workers.append(worker)

    def start(self):
        """Start audit by starting all workers."""
        for w in (self._cloud_workers + self._store_workers +
                  self._event_workers + self._alert_workers):
            w.start()

    def join(self):
        """Wait until all workers terminate."""
        # Wait for cloud workers to terminate.
        for w in self._cloud_workers:
            w.join()

        # Stop store workers and event workers.
        for q in self._store_queues + self._event_queues:
            q.put(None)

        # Wait for store workers and event_workers workers to terminate.
        for w in self._store_workers + self._event_workers:
            w.join()

        # Stop alert workers.
        for q in self._alert_queues:
            q.put(None)

        # Wait for alert workers to terminate.
        for w in self._alert_workers:
            w.join()
