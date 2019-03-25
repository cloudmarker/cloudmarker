"""SplunkStore plugin to index data in Splunk using HEC token."""

import json
import logging

import requests

_log = logging.getLogger(__name__)


class SplunkHECStore:
    """SplunkHECStore plugin to index cloud data in Splunk using HEC token."""

    def __init__(self, uri, token, index_name, ca_cert, buffer_size=1000):
        """Create an instance of :class:`SplunkHECStore` plugin.

        Arguments:
          uri (str): Splunk collector service URI.
          token (str): Splunk HEC token.
          index_name (str): Splunk HEC token accessible index.
          ca_cert (str): Location of cetificate file to verify the identity
            of host in URI, or False to disable verification
          buffer_size (int): Maximum number of records to hold in
            in-memory buffer for each record type.
        """
        self._splunk_uri = uri
        self._splunk_token = token
        self._splunk_index = index_name

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
            'index': self._splunk_index,
            'sourcetype': 'json',
            'event': record
        })

        # If the records count in self._buffer is more than allowed by
        # self._buffer_size, send those records to Splunk.
        if len(self._buffer) >= self._buffer_size:
            self._flush()

    def _flush(self):
        """Perform bulk insert of buffered records into Splunk."""
        headers = {'Authorization': 'Splunk ' + self._splunk_token}

        try:
            _log.info('Indexing %d records into %s...',
                      len(self._buffer), self._splunk_index)

            response = self._session.post(self._splunk_uri,
                                          headers=headers,
                                          data=json.dumps(self._buffer),
                                          verify=self._ca_cert)

            if response.status_code != 200:
                _log.error('POST to Splunk failed; HTTP status: %s; URI: %s;',
                           response.status_code, self._splunk_uri)
                return

            try:
                j = response.json()
            except Exception as e:
                _log.error('Failed to retrieve JSON from response: error: %s:'
                           '%s; URI: %s',
                           type(e).__name__, e, self._splunk_uri)
                return

            if j['code'] != 0:
                _log.error('Falied to index data to Splunk; error:%s; URI: %s',
                           j['text'], self._splunk_uri)
                return

            _log.info('Indexed %d records into index_name %s',
                      len(self._buffer), self._splunk_index)

            del self._buffer[:]

        except requests.ConnectionError as e:
            _log.error('Connection to Splunk failed; error: %s: %s; '
                       'URI: %s',
                       type(e).__name__, e, self._splunk_uri)

        except Exception as e:
            _log.error('Failed to index to %s; error: %s: %s',
                       self._splunk_index, type(e).__name__, e)

    def done(self):
        """Flush any remaining records."""
        self._flush()
