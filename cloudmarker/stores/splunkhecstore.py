"""SplunkStore plugin to index data in Splunk using HEC token."""

import json
import logging

import requests

_log = logging.getLogger(__name__)


class SplunkHECStore:
    """SplunkHECStore plugin to index cloud data in Splunk using HEC token."""

    def __init__(self, uri, token, index, ca_cert, buffer_size=1000):
        """Create an instance of :class:`SplunkHECStore` plugin.

        Arguments:
          uri (str): Splunk collector service URI.
          token (str): Splunk HEC token.
          index (str): Splunk HEC token accessible index.
          ca_cert (str): Location of cetificate file to verify the identity
            of host in URI, or False to disable verification
          buffer_size (int): Maximum number of records to hold in
            in-memory buffer for each record type.
        """
        self._uri = uri
        self._token = token
        self._index = index

        self._ca_cert = ca_cert
        self._buffer_size = buffer_size
        self._buffer = []

        # For maintaining session between multiple _flush calls
        self._session = requests.session()

    def write(self, record):
        """Save the record in a bulk-buffer.

        Also, flush the buffer by saving its content to Splunk when the buffer
        size exceeds configured self._buffer_size

        Arguments:
          record (dict): Data to save to the Splunk.

        """
        # Make Splunk ready payload data and append it to self._buffers list.
        self._buffer.append({
            'index': self._index,
            'sourcetype': 'json',
            'event': record
        })

        # If the records count in self._buffer is more than allowed by
        # self._buffer_size, send those records to Splunk.
        if len(self._buffer) >= self._buffer_size:
            self._flush()

    def _flush(self):
        """Perform bulk insert of buffered records into Splunk."""
        buffer_len = len(self._buffer)

        if buffer_len == 0:
            _log.info('No pending records to index; URI: %s; index: %s',
                      self._uri, self._index)
            return

        _log.info('Indexing %d records; URI: %s; index: %s ...',
                  buffer_len, self._uri, self._index)

        headers = {'Authorization': 'Splunk ' + self._token}

        try:
            response = self._session.post(self._uri,
                                          headers=headers,
                                          data=json.dumps(self._buffer),
                                          verify=self._ca_cert)

            log_data = ('URI: {}; index: {}; response status: {}; '
                        'response content: {}'
                        .format(self._uri, self._index,
                                response.status_code, response.text))

            if response.status_code != 200:
                _log.error('Failed to index %d records; HTTP status '
                           'code indicates error; %s',
                           buffer_len, log_data)
                return

            try:
                j = response.json()
            except Exception as e:
                _log.error('Failed to get JSON from response; %s; '
                           'error: %s; %s', log_data, type(e).__name__, e)
                return

            if j['code'] != 0:
                _log.error('Failed to index %d records; Splunk status '
                           'code in JSON indicates error; %s',
                           buffer_len, log_data)
                return

            _log.info('Indexed %d records; %s', buffer_len, log_data)
            del self._buffer[:]

        except requests.ConnectionError as e:
            _log.error('Failed to index %d records; connection error; '
                       'URI: %s; index: %s; error: %s: %s; ',
                       buffer_len, self._uri, self._index,
                       type(e).__name__, e)

        except Exception as e:
            _log.error('Failed to index %d records; unexpected error; '
                       'URI: %s; index: %s; error: %s: %s',
                       buffer_len, self._uri, self._index,
                       type(e).__name__, e)

    def done(self):
        """Flush any remaining records."""
        self._flush()
