"""Mock cloud plugin for testing purpose."""


class MockCloud:
    """Mock cloud plugin for testing purpose."""

    def __init__(self, record_count=10, record_types=('foo', 'bar')):
        """Initialize object of this class with specified parameters.

        Arguments:
            record_count (int): Number of mock records to generate.
            record_types (tuple): A tuple of strings that represent the
                different record types to be generated.

        """
        self._record_count = record_count
        self._record_types = record_types

    def read(self):
        """Return a record.

        This method creates and yields mock records.

        In actual cloud implementations, this method would connect to
        the cloud, retrieve JSON objects using the cloud API, and yield
        those objects.

        Yields:
            dict: Mock record.

        """
        # We try hard to keep the cloud plugins decoupled from plugins.
        # In general, we try hard to keep one plugin decoupled from
        # another plugin. However, there is still minimal coupling
        # between plugins that is unavoidable. For example, each store
        # type needs to know the type of record it is dealing with in
        # order to classify the record and put it in the right bucket
        # (an index, file, directory, etc.). Therefore, the cloud plugin
        # puts some additional metadata such as record_type into the
        # record that other plugins can rely on.
        n = len(self._record_types)
        for i in range(self._record_count):
            yield {
                'record_num': i,
                'record_type': self._record_types[i % n],
            }

    def done(self):
        """Perform clean up tasks."""
