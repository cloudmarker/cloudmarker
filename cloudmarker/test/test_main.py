"""Tests for package execution."""


import unittest
from unittest import mock


class MainTest(unittest.TestCase):
    """Tests for package execution."""

    @mock.patch('sys.argv', ['cloudmarker', '-c', 'config.base.yaml', '-n'])
    def test_main(self):
        # Run cloudmarker package with only the default base
        # configuration and ensure that it runs without issues.
        import cloudmarker.__main__
        self.assertEqual(type(cloudmarker.__main__).__name__, 'module')
