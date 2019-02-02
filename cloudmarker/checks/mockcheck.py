"""Mock check plugin for testing purpose."""


class MockCheck:
    """Mock check plugin for testing purpose."""

    def __init__(self, n=3):
        """Create an instance of :class:`MockCheck` plugin.

        This plugin checks if the ``record_num`` field of a record is a
        multiple of ``n``.

        Arguments:
            n (int): A number that the record number in mock record must
                be a multiple of in order to generate an event record.

        """
        self._n = n

    def eval(self, record):
        """Evaluate record to check for multiples of ``n``.

        If ``record['record_num']`` is a multiple of ``n`` (the
        parameter with which this plugin was initialized with), then
        generate an event record. Otherwise, do nothing.

        If ``record['record_num']`` is missing, i.e., the key named
        `record_num` does not exist, then its record number is assumed
        to be `1`.

        This is a mock example of a check plugin. In actual check
        plugins, this method would typically check for security issues
        in the ``record``.

        Arguments:
            record (dict): Record to evaluate.

        Yields:
            dict: Event record if evaluation rule matches the input
            record.

        """
        # If record number is a multiple of self._n, generate an event
        # record.
        if record.get('record_num', 1) % self._n == 0:
            yield {
                'record_type': 'mock_event',
                'n': self._n,
                'cloud_record': record,
            }

    def done(self):
        """Perform cleanup work.

        Since this is a mock plugin, this method does nothing. However,
        a typical check plugin may or may not need to perform cleanup
        work in this method depending on its nature of work.
        """
