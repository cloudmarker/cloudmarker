"""Tests for ioworkers module."""

import unittest

from cloudmarker import ioworkers


class UtilTest(unittest.TestCase):
    """Tests for util module."""

    def test_run_default_workers(self):
        out = ioworkers.run(lambda: ((i,) for i in range(5)),
                            lambda x: [x**2])
        self.assertEqual(set(out), {0, 1, 4, 9, 16})

    def test_run_worker_counts(self):
        out = ioworkers.run(lambda: ((i,) for i in range(5)),
                            lambda x: [x**2], 1, 1)
        self.assertEqual(list(out), [0, 1, 4, 9, 16])
