"""Tests for worker functions."""


import multiprocessing as mp
import unittest
from unittest import mock

from cloudmarker import workers

# MockPluginClass pretends to be a mock plugin class.
MockPluginClass = mock.Mock()

# Instantiating MockPluginClass should return a mock that pretends to be
# a mock plugin object.
MockPluginClass.return_value = mock_plugin = mock.Mock()

# Plugin config dictionary that can be used to instantiate the mock
# plugin class.
plugin_config = {
    'plugin': 'cloudmarker.test.test_workers.MockPluginClass',
}


class WorkersTest(unittest.TestCase):
    """Tests for worker functions."""

    def setUp(self):
        # Reset the call history for the mock plugin class and mock
        # plugin object.
        mock_plugin.reset_mock()
        MockPluginClass.reset_mock()

    def test_cloud_worker(self):
        # Mock plugin that generates mock records.
        mock_records = [
            {'raw': {'data': 'record1'}},
            {'raw': {'data': 'record2'}}
        ]
        mock_plugin.read.return_value = mock_records

        # Test output queues for the mock plugin.
        out_q1 = mp.Queue()
        out_q2 = mp.Queue()

        # Invoke the mock plugin with the worker.
        workers.cloud_worker('fooaudit', 'fooversion', 'foocloud',
                             plugin_config, [out_q1, out_q2])

        # Test that the worker instantiated the mock plugin class, then
        # invoked the mock plugin's read() method, and finally invoked
        # the mock plugin's done() method.
        expected_calls = [mock.call(),
                          mock.call().read(),
                          mock.call().done()]
        self.assertEqual(MockPluginClass.mock_calls, expected_calls)

        # Test that the worker has put the two string records in both
        # the test output queues.
        self.assertEqual(out_q1.get()['raw'], {'data': 'record1'})
        self.assertEqual(out_q1.get()['raw'], {'data': 'record2'})
        self.assertEqual(out_q2.get()['raw'], {'data': 'record1'})
        self.assertEqual(out_q2.get()['raw'], {'data': 'record2'})

    def test_store_worker(self):
        # Test input queue for the mock plugin.
        in_q = mp.Queue()

        # Put two mock records and None in the test input queue.
        in_q.put({'raw': {'data': 'record1'}})
        in_q.put({'raw': {'data': 'record2'}})
        in_q.put(None)

        # Invoke the mock plugin with the worker.
        workers.store_worker('fooaudit', 'fooversion', 'foostore',
                             plugin_config, in_q)

        # Test that the worker instantiated the mock plugin class, then
        # invoked the mock plugin's write() method twice (once for each
        # record), and finally invoked the mock plugin's done() method
        # (for the None input).
        expected_calls = [mock.call(),
                          mock.call().write(mock.ANY),
                          mock.call().write(mock.ANY),
                          mock.call().done()]
        self.assertEqual(MockPluginClass.mock_calls, expected_calls)

    def test_alert_worker(self):
        # Test input queue for the mock plugin.
        in_q = mp.Queue()

        # Put two mock records and None in the test input queue.
        in_q.put({'raw': {'data': 'record1'}})
        in_q.put({'raw': {'data': 'record2'}})
        in_q.put(None)

        # Invoke the mock plugin with the worker.
        workers.alert_worker('fooaudit', 'fooversion', 'fooalert',
                             plugin_config, in_q)

        # Test that the worker instantiated the mock plugin class, then
        # invoked the mock plugin's write() method twice (once for each
        # record), and finally invoked the mock plugin's done() method
        # (for the None input).
        expected_calls = [mock.call(),
                          mock.call().write(mock.ANY),
                          mock.call().write(mock.ANY),
                          mock.call().done()]
        self.assertEqual(MockPluginClass.mock_calls, expected_calls)

    def test_event_worker(self):
        # A fake_eval function that returns two fake records: length of
        # input string, and upper-cased input string.
        def fake_eval(s):
            yield {'ext': {'len': len(s)}}
            yield {'ext': {'upper': s.upper()}}

        # Mock plugin.
        mock_plugin.eval = mock.Mock(side_effect=fake_eval)

        # Test input queue and output queues for the mock plugin.
        in_q = mp.Queue()
        out_q1 = mp.Queue()
        out_q2 = mp.Queue()

        # Put two string records and None in the test input queue.
        in_q.put('record1')
        in_q.put('record2')
        in_q.put(None)

        # Invoke the mock plugin with the worker.
        workers.event_worker('fooaudit', 'fooversion', 'fooevent',
                             plugin_config, in_q, [out_q1, out_q2])

        # Test that the worker instantiated the mock plugin class, then
        # invoked the mock plugin's eval() method twice (once for each
        # input string record), and finally invoked the mock plugin's
        # done() method (for the None input).
        expected_calls = [mock.call(),
                          mock.call().eval('record1'),
                          mock.call().eval('record2'),
                          mock.call().done()]
        self.assertEqual(MockPluginClass.mock_calls, expected_calls)

        # Test that the worker has put the values yielded by fake_eval
        # in the test output queues.
        self.assertEqual(out_q1.get()['ext'], {'len': 7})
        self.assertEqual(out_q1.get()['ext'], {'upper': 'RECORD1'})
        self.assertEqual(out_q1.get()['ext'], {'len': 7})
        self.assertEqual(out_q1.get()['ext'], {'upper': 'RECORD2'})
        self.assertEqual(out_q2.get()['ext'], {'len': 7})
        self.assertEqual(out_q2.get()['ext'], {'upper': 'RECORD1'})
        self.assertEqual(out_q2.get()['ext'], {'len': 7})
        self.assertEqual(out_q2.get()['ext'], {'upper': 'RECORD2'})
