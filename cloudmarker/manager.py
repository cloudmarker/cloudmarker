#!/usr/bin/env python


"""Manager of worker subprocesses.

This module invokes the worker subprocesses that perform the cloud
security monitoring tasks. Each worker subprocess wraps around a cloud,
store, event, or alert plugin and executes the plugin in a separate
subprocess.
"""


import copy
import logging.config
import multiprocessing as mp
import textwrap
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
    log_config = copy.deepcopy(baseconfig.config_dict['logger'])
    log_config['handlers'] = {'console': log_config['handlers']['console']}
    log_config['root']['handlers'] = ['console']
    logging.config.dictConfig(log_config)
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
    _log.info('Cloudmarker %s; configured', cloudmarker.__version__)

    # Finally, run the audits, either right now or as per a schedule,
    # depending on the command line options.
    if args.now:
        _log.info('Starting job now')
        _run(config)
    else:
        _log.info('Scheduled to run job everyday at %s', config['schedule'])
        schedule.every().day.at(config['schedule']).do(_run, config)
        while True:
            schedule.run_pending()
            time.sleep(60)


def _run(config):
    """Run the audits.

    Arguments:
        config (dict): Configuration dictionary.
    """
    start_time = time.localtime()
    _send_email(config.get('email'), 'all audits', start_time)

    # Create an audit object for each audit configured to be run.
    audit_version = time.strftime('%Y%m%d_%H%M%S', time.gmtime())
    audits = []
    for audit_key in config['run']:
        audits.append(Audit(audit_key, audit_version, config))

    # Start all audits.
    for audit in audits:
        audit.start()

    # Wait for all audits to terminate.
    for audit in audits:
        audit.join()

    end_time = time.localtime()
    _send_email(config.get('email'), 'all audits', start_time, end_time)


class Audit:
    """Audit manager.

    This class encapsulates a set of worker subprocesses and worker
    input queues for a single audit configuration.
    """

    def __init__(self, audit_key, audit_version, config):
        """Create an instance of :class:`Audit` from configuration.

        A single audit definition (from a list of audit definitions
        under the ``audits`` key in the configuration) is instantiated.
        Each audit definition contains lists of cloud plugins, store
        plugins, event plugins, and alert plugins. These plugins are
        instantiated and multiprocessing queues are set up to take
        records from one plugin and feed them to another plugin as per
        the audit workflow.

        Arguments:
            audit_key (str): Key name for an audit configuration. This
                key is looked for in ``config['audits']``.
            audit_version (str): Audit version string.
            config (dict): Configuration dictionary. This is the
                entire configuration dictionary that contains
                top-level keys named ``clouds``, ``stores``, ``events``,
                ``alerts``, ``audits``, ``run``, etc.
        """
        self._start_time = time.localtime()
        self._audit_key = audit_key
        self._audit_version = audit_version
        self._config = config
        audit_config = config['audits'][audit_key]

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
        for plugin_key in audit_config.get('alerts', []):
            input_queue = mp.Queue()
            args = (
                audit_key,
                audit_version,
                plugin_key,
                util.load_plugin(config['plugins'][plugin_key]),
                input_queue,
            )
            worker = mp.Process(target=workers.alert_worker, args=args)
            self._alert_workers.append(worker)
            self._alert_queues.append(input_queue)

        # Create event_workers workers and queues.
        for plugin_key in audit_config.get('events', []):
            input_queue = mp.Queue()
            args = (
                audit_key,
                audit_version,
                plugin_key,
                util.load_plugin(config['plugins'][plugin_key]),
                input_queue,
                self._alert_queues,
            )
            worker = mp.Process(target=workers.event_worker, args=args)
            self._event_workers.append(worker)
            self._event_queues.append(input_queue)

        # Create store workers and queues.
        for plugin_key in audit_config.get('stores', []):
            input_queue = mp.Queue()
            args = (
                audit_key,
                audit_version,
                plugin_key,
                util.load_plugin(config['plugins'][plugin_key]),
                input_queue,
            )
            worker = mp.Process(target=workers.store_worker, args=args)
            self._store_workers.append(worker)
            self._store_queues.append(input_queue)

        # Create cloud workers.
        for plugin_key in audit_config.get('clouds', []):
            args = (
                audit_key,
                audit_version,
                plugin_key,
                util.load_plugin(config['plugins'][plugin_key]),
                self._store_queues + self._event_queues
            )
            worker = mp.Process(target=workers.cloud_worker, args=args)
            self._cloud_workers.append(worker)

    def start(self):
        """Start audit by starting all workers."""
        _send_email(self._config.get('email'), self._audit_key,
                    self._start_time)

        begin_record = {'com': {'record_type': 'begin_audit'}}

        # Start store and alert workers first before cloud and event
        # workers. See next comment to know why.
        for w in self._store_workers + self._alert_workers:
            w.start()

        # We want to send begin_audit record to store/alert plugins
        # before any cloud/event workers can send their records to them.
        for q in self._store_queues + self._alert_queues:
            q.put(begin_record)

        # Now start the cloud and event workers.
        for w in self._cloud_workers + self._event_workers:
            w.start()

    def join(self):
        """Wait until all workers terminate."""
        # Wait for cloud workers to terminate.
        for w in self._cloud_workers:
            w.join()

        end_record = {'com': {'record_type': 'end_audit'}}

        # Stop store workers.
        for q in self._store_queues:
            q.put(end_record)
            q.put(None)

        # Stop event workers.
        for q in self._event_queues:
            q.put(None)

        # Wait for store workers to terminate.
        for w in self._store_workers:
            w.join()

        # Wait for event workers to terminate.
        for w in self._event_workers:
            w.join()

        # Stop alert workers.
        for q in self._alert_queues:
            q.put(end_record)
            q.put(None)

        # Wait for alert workers to terminate.
        for w in self._alert_workers:
            w.join()

        end_time = time.localtime()
        _send_email(self._config.get('email'), self._audit_key,
                    self._start_time, end_time)


def _send_email(email_config, about, start_time, end_time=None):
    """Send email about job or audit that is starting or ending.

    Arguments:
        email_config (dict): Top-level email configuration dictionary.
        about (str): A short string that says what the email
            notification is about, e.g., ``'job'`` or ``'audit'``.
        start_time (time.struct_time): Start time of job or audit.
        end_time (time.struct_time): End time of job or audit. This
            argument must not be specified if the job or audit is
            starting.
    """
    state = 'starting' if end_time is None else 'ending'
    if email_config is None:
        _log.info('Skipping email notification because email config is '
                  'missing; about: %s; state: %s', about, state)
        return

    _log.info('Sending email; about: %s; state: %s', about, state)

    # This part of the content is common for both starting and
    # ending states.
    time_fmt = '%Y-%m-%d %H:%M:%S %z (%Z)'
    content = """
    About: {}
    Started: {}
    """.format(about, time.strftime(time_fmt, start_time))
    content = textwrap.dedent(content).lstrip()

    # This part of the content is added only for ending state.
    if state == 'ending':
        duration = time.mktime(end_time) - time.mktime(start_time)
        mm, ss = divmod(duration, 60)
        hh, mm = divmod(mm, 60)

        end_content = """
        Ended: {}
        Duration: {:02.0f} h {:02.0f} m {:02.0f} s
        """.format(time.strftime(time_fmt, end_time), hh, mm, ss)

        content = content + textwrap.dedent(end_content).lstrip()

    util.send_email(content=content, **email_config)
    _log.info('Sent email; about: %s; state: %s', about, state)
