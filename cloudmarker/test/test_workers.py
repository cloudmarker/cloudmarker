"""Tests for worker functions."""


import multiprocessing as mp
import unittest
from unittest import mock

from cloudmarker import workers


class WorkersTest(unittest.TestCase):
    """Tests for worker functions."""

    def test_cloud_worker(self):
        # Mock plugin that generates two string records.
        plugin = mock.Mock()
        plugin.read = mock.Mock(return_value=['record1', 'record2'])

        # Test output queues for the mock plugin.
        out_q1 = mp.Queue()
        out_q2 = mp.Queue()

        # Invoke the mock plugin with the worker.
        workers.cloud_worker('foo', plugin, [out_q1, out_q2])

        # Test that the worker invoked the mock plugin's read() method
        # and finally invoked the mock plugin's done() method.
        expected_calls = [mock.call.read(),
                          mock.call.done()]
        self.assertEqual(plugin.mock_calls, expected_calls)

        # Test that the worker has put the two string records in both
        # the test output queues.
        self.assertEqual(out_q1.get(), 'record1')
        self.assertEqual(out_q1.get(), 'record2')
        self.assertEqual(out_q2.get(), 'record1')
        self.assertEqual(out_q2.get(), 'record2')

    def test_store_worker(self):
        # Mock plugin.
        plugin = mock.Mock()

        # Test input queue for the mock plugin.
        in_q = mp.Queue()

        # Put two string records and None in the test input queue.
        in_q.put('record1')
        in_q.put('record2')
        in_q.put(None)

        # Invoke the mock plugin with the worker.
        workers.store_worker('foo', plugin, in_q)

        # Test that the worker invoked the mock plugin's write()
        # method twice (once with each string record) and finally
        # invoked the mock plugin's done() method (for the None input).
        expected_calls = [mock.call.write('record1'),
                          mock.call.write('record2'),
                          mock.call.done()]
        self.assertEqual(plugin.mock_calls, expected_calls)

    def test_check_worker(self):
        # A fake_eval function that returns two fake records: length of
        # input string, and upper-cased input string.
        def fake_eval(s):
            yield len(s)
            yield s.upper()

        # Mock plugin.
        plugin = mock.Mock()
        plugin.eval = mock.Mock(side_effect=fake_eval)

        # Test input queue and output queues for the mock plugin.
        in_q = mp.Queue()
        out_q1 = mp.Queue()
        out_q2 = mp.Queue()

        # Put two string records and None in the tet input queue.
        in_q.put('record1')
        in_q.put('record2')
        in_q.put(None)

        # Invoke the mock plugin with the worker.
        workers.check_worker('foo', plugin, in_q, [out_q1, out_q2])

        # Test that the worker invoked the mock plugin's eval() method
        # twice (once for each input string record) and finally invoked
        # the mock plugin's done() method (for the None input).
        expected_calls = [mock.call.eval('record1'),
                          mock.call.eval('record2'),
                          mock.call.done()]
        self.assertEqual(plugin.mock_calls, expected_calls)

        # Test that the worker has put the values yielded by fake_eval
        # in the test output queues.
        self.assertEqual(out_q1.get(), 7)
        self.assertEqual(out_q1.get(), 'RECORD1')
        self.assertEqual(out_q1.get(), 7)
        self.assertEqual(out_q1.get(), 'RECORD2')
        self.assertEqual(out_q2.get(), 7)
        self.assertEqual(out_q2.get(), 'RECORD1')
        self.assertEqual(out_q2.get(), 7)
        self.assertEqual(out_q2.get(), 'RECORD2')
