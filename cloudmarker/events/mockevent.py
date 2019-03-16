"""Mock event plugin for testing purpose."""


class MockEvent:
    """Mock event plugin for testing purpose."""

    def __init__(self, n=3):
        """Create an instance of :class:`MockEvent` plugin.

        This plugin events if the ``data`` field of a mock record is a
        multiple of ``n``.

        Arguments:
            n (int): A number that the record data value in mock record
                must be a multiple of in order to generate an event record.

        """
        self._n = n

    def eval(self, record):
        """Evaluate record to check for multiples of ``n``.

        If ``record['raw']['data']`` is a multiple of ``n`` (the
        parameter with which this plugin was initialized with), then
        generate an event record. Otherwise, do nothing.

        If ``record['raw']['data]`` is missing, i.e., the key named
        ``raw`` or ``data`` does not exist, then its record number is
        assumed to be ``1``.

        This is a mock example of a event plugin. In actual event
        plugins, this method would typically check for security issues
        in the ``record``.

        Arguments:
            record (dict): Record to evaluate.

        Yields:
            dict: Event record if evaluation rule matches the input
            record.

        """
        # If record data value is a multiple of self._n, generate an
        # event record.
        if record.get('raw', {}).get('data', 1) % self._n == 0:
            yield {
                'ext': {
                    'record_type': 'mock_event',
                    'n': self._n,
                    'cloud_record': record
                },
                'com': {
                    'record_type': 'mock_event'
                }
            }

    def done(self):
        """Perform cleanup work.

        Since this is a mock plugin, this method does nothing. However,
        a typical event plugin may or may not need to perform cleanup
        work in this method depending on its nature of work.
        """
