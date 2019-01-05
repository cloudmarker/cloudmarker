"""Tests for setup configuration script."""


import glob
import shutil
import unittest
from unittest import mock


class MainTest(unittest.TestCase):
    """Tests for package execution."""

    def setUp(self):
        shutil.rmtree('dist', ignore_errors=True)

    def tearDown(self):
        shutil.rmtree('dist', ignore_errors=True)

    @mock.patch('sys.argv', ['setup.py', 'sdist', 'bdist_wheel'])
    def test_setup(self):
        import setup
        self.assertEqual(type(setup).__name__, 'module')
        self.assertEqual(len(glob.glob('dist/*.whl')), 1)
        self.assertEqual(len(glob.glob('dist/*.tar.gz')), 1)
