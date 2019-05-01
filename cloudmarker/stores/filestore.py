"""Filesystem store plugin."""


import json
import os
import os.path


class FileStore:
    """A plugin to store records on the filesystem."""

    def __init__(self, path='/tmp/cloudmarker'):
        """Create an instance of :class:`FileStore` plugin.

        Arguments:
            path (str): Path of directory where files are written to.

        """
        self._path = os.path.expanduser(path)
        self._worker_names = set()
        os.makedirs(self._path, exist_ok=True)

    def write(self, record):
        """Write JSON records to the file system.

        This method is called once for every ``record`` read from a
        cloud. In this example implementation of a store, we simply
        write the ``record`` in JSON format to a file. The list of
        records is maintained as JSON array in the file. The origin
        worker name in ``record['com']['origin_worker']`` is used to
        determine the filename.

        The records are written to a ``.tmp`` file because we don't want
        to delete the existing complete and useful ``.json`` file
        prematurely.

        Note that other implementations of a store may choose to buffer
        the records in memory instead of writing each record to the
        store immediately. They may then flush the buffer to the store
        based on certain conditions such as buffer size, time interval,
        etc.

        Arguments:
            record (dict): Data to write to the file system.

        """
        worker_name = record.get('com', {}).get('origin_worker', 'no_worker')

        tmp_file_path = os.path.join(self._path, worker_name) + '.tmp'
        if worker_name not in self._worker_names:
            # If this is the first time we have encountered this
            # worker_name, we create a new file for it and write an
            # opening bracket to start a JSON array.
            with open(tmp_file_path, 'w') as f:
                f.write('[\n')
            delim = ''
        else:
            # If this is not the first record of its record type, then
            # we need to separate this record from the previous record
            # with a comma to form a valid JSON array.
            delim = ',\n'

        # Write the record dictionary as JSON object literal.
        self._worker_names.add(worker_name)
        with open(tmp_file_path, 'a') as f:
            f.write(delim + json.dumps(record, indent=2))

    def done(self):
        """Perform final cleanup tasks.

        This method is called after all records have been written. In
        this example implementation, we properly terminate the JSON
        array in the .tmp file. Then we rename the .tmp file to .json
        file.

        Note that other implementations of a store may perform tasks
        like closing a connection to a remote store or flushing any
        remaining records in a buffer.

        """
        for worker_name in self._worker_names:
            # End the JSON array by writing a closing bracket.
            tmp_file_path = os.path.join(self._path, worker_name) + '.tmp'
            with open(tmp_file_path, 'a') as f:
                f.write('\n]\n')

            # Rename the temporary file to a JSON file.
            json_file_path = os.path.join(self._path, worker_name) + '.json'
            os.rename(tmp_file_path, json_file_path)
