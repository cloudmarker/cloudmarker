"""Worker functions.

The functions in this module wrap around plugin classes such that these
worker functions can be specified as the ``target`` parameter while
launching a new subprocess with :class:`multiprocessing.Process`.

Each worker function can run as a separate subprocess. While wrapping
around a plugin class, each worker function creates the multiprocessing
queues necessary to pass records from one plugin class to another.
"""


import logging

from cloudmarker import util

_log = logging.getLogger(__name__)


def cloud_worker(audit_key, audit_version, plugin_key, plugin,
                 output_queues):
    """Worker function for cloud plugins.

    This function expects the ``plugin`` object to implement a ``read``
    method that yields records. This function calls this ``read`` method
    to retrieve records and puts each record into each queue in
    ``output_queues``.

    Arguments:
        audit_key (str): Audit key name in configuration.
        audit_version (str): Audit version string.
        plugin_key (str): Plugin key name in configuration.
        plugin (object): Cloud plugin object.
        output_queues (list): List of :class:`multiprocessing.Queue`
            objects to write records to.
    """
    worker_name = audit_key + '_' + plugin_key
    _log.info('%s: Started', worker_name)
    try:
        for record in plugin.read():
            record['com'] = util.merge_dicts(record.get('com', {}), {
                'audit_key': audit_key,
                'audit_version': audit_version,
                'origin_key': plugin_key,
                'origin_class': type(plugin).__name__,
                'origin_worker': worker_name,
                'origin_type': 'cloud',
            })
            for q in output_queues:
                q.put(record)
    except Exception as e:
        _log.exception('%s: Failed; read() error: %s: %s',
                       worker_name, type(e).__name__, e)

    try:
        plugin.done()
    except Exception as e:
        _log.exception('%s: Failed; done() error: %s: %s',
                       worker_name, type(e).__name__, e)

    _log.info('%s: Stopped', worker_name)


def event_worker(audit_key, audit_version, plugin_key, plugin,
                 input_queue, output_queues):
    """Worker function for event plugins.

    This function expects the ``plugin`` object to implement a ``eval``
    method that accepts a single record as a parameter and yields one or
    more records, and a ``done`` method to perform cleanup work in the
    end.

    This function gets records from ``input_queue`` and passes each
    record to the ``eval`` method of ``plugin``. Then it puts each
    record yielded by the ``eval`` method into each queue in
    ``output_queues``.

    When there are no more records in the ``input_queue``, i.e., once
    ``None`` is found in the ``input_queue``, this function calls the
    ``done`` method of the ``plugin`` to indicate that record
    processing is over.

    Arguments:
        audit_key (str): Audit key name in configuration.
        audit_version (str): Audit version string.
        plugin_key (str): Plugin key name in configuration.
        plugin (object): Store plugin object.
        input_queue (multiprocessing.Queue): Queue to read records from.
        output_queues (list): List of :class:`multiprocessing.Queue`
            objects to write records to.
    """
    worker_name = audit_key + '_' + plugin_key
    _log.info('%s: Started', worker_name)
    while True:
        record = input_queue.get()
        if record is None:
            try:
                plugin.done()
            except Exception as e:
                _log.exception('%s: Failed; done() error: %s: %s',
                               worker_name, type(e).__name__, e)
            break

        try:
            for event_record in plugin.eval(record):
                event_record['com'] = \
                    util.merge_dicts(event_record.get('com', {}), {
                        'audit_key': audit_key,
                        'audit_version': audit_version,
                        'origin_key': plugin_key,
                        'origin_class': type(plugin).__name__,
                        'origin_worker': worker_name,
                        'origin_type': 'event',
                    })
                for q in output_queues:
                    q.put(event_record)
        except Exception as e:
            _log.exception('%s: Failed; eval() error: %s: %s',
                           worker_name, type(e).__name__, e)

    _log.info('%s: Stopped', worker_name)


def store_worker(audit_key, audit_version, plugin_key, plugin,
                 input_queue):
    """Worker function for store plugins.

    This function expects the ``plugin`` object to implement a
    ``write`` method that accepts a single record as a parameter and a
    ``done`` method to perform cleanup work in the end.

    This function gets records from ``input_queue`` and passes each
    record to the ``write`` method of ``plugin``.

    When there are no more records in the ``input_queue``, i.e., once
    ``None`` is found in the ``input_queue``, this function calls the
    ``done`` method of the ``plugin`` to indicate that record
    processing is over.

    Arguments:
        audit_key (str): Audit key name in configuration.
        audit_version (str): Audit version string.
        plugin_key (str): Plugin key name in configuration.
        plugin (object): Store plugin object.
        input_queue (multiprocessing.Queue): Queue to read records from.
    """
    _write_worker(audit_key, audit_version, plugin_key, plugin,
                  input_queue, 'store')


def alert_worker(audit_key, audit_version, plugin_key, plugin,
                 input_queue):
    """Worker function for alert plugins.

    This function behaves like :func:`cloudmarker.workers.store_worker`.
    See its documentation for details.

    Arguments:
        audit_key (str): Audit key name in configuration.
        audit_version (str): Audit version string.
        plugin_key (str): Plugin key name in configuration.
        plugin (object): Alert plugin object.
        input_queue (multiprocessing.Queue): Queue to read records from.
    """
    _write_worker(audit_key, audit_version, plugin_key, plugin,
                  input_queue, 'alert')


def _write_worker(audit_key, audit_version, plugin_key, plugin,
                  input_queue, worker_type):
    """Worker function for store and alert plugins.

    Arguments:
        audit_key (str): Audit key name in configuration
        audit_version (str): Audit version string.
        plugin_key (str): Plugin key name in configuration.
        plugin (object): Store plugin or alert plugin object.
        input_queue (multiprocessing.Queue): Queue to read records from.
        worker_type (str): Either ``'store'`` or ``'alert'``.
    """
    worker_name = audit_key + '_' + plugin_key
    _log.info('%s: Started', worker_name)
    while True:
        record = input_queue.get()
        if record is None:
            try:
                plugin.done()
            except Exception as e:
                _log.exception('%s: Failed; done() error: %s: %s',
                               worker_name, type(e).__name__, e)
            break

        record['com'] = util.merge_dicts(record.get('com', {}), {
            'audit_key': audit_key,
            'audit_version': audit_version,
            'target_key': plugin_key,
            'target_class': type(plugin).__name__,
            'target_worker': worker_name,
            'target_type': worker_type,
        })

        try:
            plugin.write(record)
        except Exception as e:
            _log.exception('%s: Failed; write() error: %s: %s',
                           worker_name, type(e).__name__, e)
    _log.info('%s: Stopped', worker_name)
