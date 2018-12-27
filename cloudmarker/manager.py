#!/usr/bin/env python


"""Manager of worker processes.

This module invokes the worker processes that perform the cloud security
monitoring tasks.
"""


import multiprocessing as mp

from cloudmarker import util, workers


def main():
    """Run the framework."""
    args = util.parse_cli()
    config = util.load_config(args.config)

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

    This class encapsulates a set of worker processes and worker input
    queues for a single audit configuration.
    """

    def __init__(self, audit_name, config):
        """Initialize a single audit manager from configuration.

        Arguments:
            audit_name (str): Key name for an audit configuration. This
                key is looked for in ``config['audits']``.
            config (dict): Configuration dictionary. This is the
                entire configuration dictionary that contains
                top-level keys named ``clouds``, ``stores``, ``checks``,
                 ``alerts``, ``audits``, ``run``, etc.
        """
        audit_config = config['audits'][audit_name]

        # We keep all workers in these lists.
        self._cloud_workers = []
        self._store_workers = []
        self._check_workers = []
        self._alert_workers = []

        # We keep all queues in these lists.
        self._store_queues = []
        self._check_queues = []
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

        # Create check workers and queues.
        for name in audit_config['checks']:
            input_queue = mp.Queue()
            args = (
                audit_name + '-' + name,
                util.load_plugin(config['checks'][name]),
                input_queue,
                self._alert_queues,
            )
            worker = mp.Process(target=workers.check_worker, args=args)
            self._check_workers.append(worker)
            self._check_queues.append(input_queue)

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
            input_queue = mp.Queue()
            args = (
                audit_name + '-' + name,
                util.load_plugin(config['clouds'][name]),
                self._store_queues + self._check_queues
            )
            worker = mp.Process(target=workers.cloud_worker, args=args)
            self._cloud_workers.append(worker)

    def start(self):
        """Start audit by starting all workers."""
        for w in (self._cloud_workers + self._store_workers +
                  self._check_workers + self._alert_workers):
            w.start()

    def join(self):
        """Wait until all workers terminate."""
        # Wait for cloud workers to terminate.
        for w in self._cloud_workers:
            w.join()

        # Stop store workers and check workers.
        for q in self._store_queues + self._check_queues:
            q.put(None)

        # Wait for store workers and check workers to terminate.
        for w in self._store_workers + self._check_workers:
            w.join()

        # Stop alert workers.
        for q in self._alert_queues:
            q.put(None)

        # Wait for alert workers to terminate.
        for w in self._alert_workers:
            w.join()
