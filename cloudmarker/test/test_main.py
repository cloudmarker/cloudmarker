"""Tests for package execution."""


import importlib
import unittest
from unittest import mock


class MainTest(unittest.TestCase):
    """Tests for package execution."""

    @mock.patch('sys.argv', ['cloudmarker', '-c', '-n'])
    def test_main(self):
        # Run cloudmarker package with only the default base
        # configuration and ensure that it runs without issues.
        module = importlib.import_module('cloudmarker.__main__')
        self.assertEqual(type(module).__name__, 'module')
