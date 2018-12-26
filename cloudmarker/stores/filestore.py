"""Filesystem store plugin."""


import json
import os


class FileStore:
    """A plugin to store records on the filesystem."""

    def __init__(self, path='/tmp/cloudmarker'):
        """Initialize object of this class with specified parameters.

        Arguments:
            path (str): Path of directory where files are written to.

        """
        self._path = path
        self._record_types = set()
        os.makedirs(path, exist_ok=True)

    def write(self, record):
        """Write JSON records to the file system.

        This method is called once for every ``record`` read from a
        cloud. In this example implementation of a store, we simply
        write the ``record`` in JSON format to a file. The list of
        records is maintained as JSON array in the file. The record
        type, i.e., ``record['record_type']`` is used to determine the
        filename.

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
        record_type = record['record_type']

        # If this is the first time we have encountered this
        # record_type, we create a new file for it and write an opening
        # bracket to start a JSON array.
        tmp_file_path = os.path.join(self._path, record_type) + '.tmp'
        if record_type not in self._record_types:
            with open(tmp_file_path, 'w') as f:
                f.write('[\n')

        # Write the record dictionary as JSON object literal.
        self._record_types.add(record_type)
        with open(tmp_file_path, 'a') as f:
            f.write(json.dumps(record, indent=2) + ',\n')

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
        for record_type in self._record_types:
            # End the JSON array by writing a closing bracket.
            tmp_file_path = os.path.join(self._path, record_type) + '.tmp'
            with open(tmp_file_path, 'a') as f:
                f.write(']\n')

            # Rename the temporary file to a JSON file.
            json_file_path = os.path.join(self._path, record_type) + '.json'
            os.rename(tmp_file_path, json_file_path)
