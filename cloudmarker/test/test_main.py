"""Tests for package execution."""


import unittest
from unittest import mock


class MainTest(unittest.TestCase):
    """Tests for package execution."""

    @mock.patch('sys.argv', ['cloudmarker', '-c', 'config.base.yaml'])
    def test_main(self):
        # Run cloudmarker package with only the default base
        # configuration and ensure that it runs without issues.
        import cloudmarker.__main__

        # Check that __version__ is defined.
        self.assertTrue(len(cloudmarker.__main__.__version__) > 0)
