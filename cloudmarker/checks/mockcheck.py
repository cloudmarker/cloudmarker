"""Mock check plugin for testing purpose."""


class MockCheck:
    """Mock check plugin for testing purpose."""

    def __init__(self, n=3):
        """Initialize object of this class with specified parameters.

        This is a mock check for mock records only that checks if the
        record number in the mock record is a multiple of ``n``.

        Arguments:
            n (int): A number that the record number in mock record must
                be a multiple of in order to generate an event record.

        """
        self._n = n

    def eval(self, record):
        """Evaluate record to check for multiples of n.

        Arguments:
            record (dict): Record to evaluate.

        Yields:
            dict: An event record whenever the check rule matches the
                input record being evaluated.

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
        """Perform clean up tasks."""
