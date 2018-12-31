"""Worker functions.

The functions in this module wrap around plugin classes such that these
worker functions can be specified as the ``target`` parameter while
launching a new process with ``multiprocessing.Process``.

Each worker function can run as a separate process. While wrapping
around a plugin class, each worker function creates the appropriate
multiprocessing queues to pass records from one plugin class to another.
"""


import logging

_logger = logging.getLogger(__name__)


def cloud_worker(worker_name, cloud_plugin, output_queues):
    """Cloud worker function.

    Arguments:
        worker_name (str): Display name for the worker.
        cloud_plugin (object): Cloud plugin object.
        output_queues (list): List of mp.Queue objects to write records to.
    """
    _logger.info('%s: Started', worker_name)
    for record in cloud_plugin.read():
        for q in output_queues:
            q.put(record)
    _logger.info('%s: Stopped', worker_name)


def store_worker(worker_name, store_plugin, input_queue):
    """Store worker function.

    Arguments:
        worker_name (str): Display name for the worker.
        store_plugin (object): Store plugin object.
        input_queue (multiprocessing.Queue): Queue to read records from.
    """
    _logger.info('%s: Started', worker_name)
    while True:
        record = input_queue.get()
        if record is None:
            store_plugin.done()
            break
        store_plugin.write(record)
    _logger.info('%s: Stopped', worker_name)


def check_worker(worker_name, check_plugin, input_queue, output_queues):
    """Check worker function.

    Arguments:
        worker_name (str): Display name for the worker.
        store_plugin (object): Store plugin object.
        input_queue (multiprocessing.Queue): Queue to read records from.
        output_queues (list): List of queues to write event records to.
    """
    _logger.info('%s: Started', worker_name)
    while True:
        record = input_queue.get()
        if record is None:
            check_plugin.done()
            break

        for event_record in check_plugin.eval(record):
            for q in output_queues:
                q.put(event_record)

    _logger.info('%s: Stopped', worker_name)
