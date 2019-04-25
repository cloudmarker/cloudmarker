"""Email alert plugin."""


import logging

from cloudmarker import util

# Define module-level logger.
_log = logging.getLogger(__name__)


class EmailAlert:
    """A plugin to send email alerts."""

    def __init__(self, **kwargs):
        """Create an instance of :class:`EmailAlert` plugin.

        This class accepts the same arguments as
        :func:`cloudmarker.util.send_email`.

        The ``content`` argument is not honoured. Even if a ``content``
        argument is provided, it is ignored by this class because this
        class defines its own content from the event records it receives
        in its :meth:`write` method.
        """
        self._kwargs = kwargs
        self._buffer = []

    def write(self, record):
        """Save event record in a buffer.

        Arguments:
            record (dict): An event record.
        """
        for _, value in record.items():
            self._buffer.append(repr(value))

    def done(self):
        """Send the buffered events as an email alert."""
        self._kwargs['content'] = '\n\n'.join(self._buffer)
        util.send_email(**self._kwargs)
