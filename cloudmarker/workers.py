"""Worker functions.

The functions in this module wrap around plugin classes such that these
worker functions can be specified as the ``target`` parameter while
launching a new subprocess with :class:`multiprocessing.Process`.

Each worker function can run as a separate subprocess. While wrapping
around a plugin class, each worker function creates the multiprocessing
queues necessary to pass records from one plugin class to another.
"""


import logging

_log = logging.getLogger(__name__)


def cloud_worker(worker_name, cloud_plugin, output_queues):
    """Worker function for cloud plugins.

    This function expects the ``cloud_plugin`` object to implement a
    ``read`` method that yields records. This function calls this
    ``read`` method to retrieve records and puts each record into each
    queue in ``output_queues``.

    Arguments:
        worker_name (str): Display name for the worker.
        cloud_plugin (object): Cloud plugin object.
        output_queues (list): List of :class:`multiprocessing.Queue`
            objects to write records to.
    """
    _log.info('%s: Started', worker_name)
    for record in cloud_plugin.read():
        record.setdefault('com', {})
        record['com']['origin_worker'] = worker_name
        record['com']['origin_type'] = 'cloud'
        record['com']['cloud_worker'] = worker_name
        for q in output_queues:
            q.put(record)
    cloud_plugin.done()
    _log.info('%s: Stopped', worker_name)


def store_worker(worker_name, store_plugin, input_queue):
    """Worker function for store plugins.

    This function expects the ``store_plugin`` object to implement a
    ``write`` method that accepts a single record as a parameter and a
    ``done`` method to perform cleanup work in the end.

    This function gets records from ``input_queue`` and passes each
    record to the ``write`` method of ``store_plugin``.

    When there are no more records in the ``input_queue``, i.e., once
    ``None`` is found in the ``input_queue``, this function calls the
    ``done`` method of the ``store_plugin`` to indicate that record
    processing is over.

    Arguments:
        worker_name (str): Display name for the worker.
        store_plugin (object): Store plugin object.
        input_queue (multiprocessing.Queue): Queue to read records from.
    """
    _log.info('%s: Started', worker_name)
    while True:
        record = input_queue.get()
        if record is None:
            store_plugin.done()
            break
        record.setdefault('com', {})
        record['com']['store_worker'] = worker_name
        store_plugin.write(record)
    _log.info('%s: Stopped', worker_name)


def event_worker(worker_name, event_plugin, input_queue, output_queues):
    """Worker function for event plugins.

    This function expects the ``event_plugin`` object to implement a
    ``eval`` method that accepts a single record as a parameter and
    yields one or more records, and a ``done`` method to perform cleanup
    work in the end.

    This function gets records from ``input_queue`` and passes each
    record to the ``eval`` method of ``event_plugin``. Then it puts each
    record yielded by the ``eval`` method into each queue in
    ``output_queues``.

    When there are no more records in the ``input_queue``, i.e., once
    ``None`` is found in the ``input_queue``, this function calls the
    ``done`` method of the ``store_plugin`` to indicate that record
    processing is over.

    Arguments:
        worker_name (str): Display name for the worker.
        store_plugin (object): Store plugin object.
        input_queue (multiprocessing.Queue): Queue to read records from.
        output_queues (list): List of :class:`multiprocessing.Queue`
            objects to write records to.
    """
    _log.info('%s: Started', worker_name)
    while True:
        record = input_queue.get()
        if record is None:
            event_plugin.done()
            break

        for event_record in event_plugin.eval(record):
            event_record.setdefault('com', {})
            event_record['com']['origin_worker'] = worker_name
            event_record['com']['origin_type'] = 'event'
            event_record['com']['event_worker'] = worker_name
            for q in output_queues:
                q.put(event_record)
    _log.info('%s: Stopped', worker_name)
