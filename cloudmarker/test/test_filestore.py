"""Tests for filestore plugin."""


import json
import os
import pathlib
import shutil
import unittest

from cloudmarker.stores import filestore


def write_to_file(filename):
    """Write a dummy data to a filename.

    Arguments:
        filename (str): the file location where dummy data has to be written

    """
    # Initialize the FileStore plugin with the filename
    store = filestore.FileStore(filename)

    # dummy data to write
    mp = {
        'raw': {
            'data': {
                'test_name': 'tilde_filename'
            }
        },
        'com': {
            'origin_worker': 'mock_worker'
        }
    }

    store.write(mp)
    store.done()


class FileStoreTest(unittest.TestCase):
    """Tests for filestore plugin."""

    def test_filepath_tilde_no_user(self):
        write_to_file("~/caramel_l33t/cloudmarker")
        # if the parsing fails, it should create a "~" directory in the current
        # path
        f = pathlib.Path("~")

        # If exists and is a directory, the parsing failed.
        self.assertFalse(f.is_dir())

    def test_filepath_tilde_user(self):
        user = os.getenv("USER")
        write_to_file("~{}/caramel_tpb/cloudmarker".format(user))
        # if the parsing fails, it should create a "~" directory in the current
        # path
        f = pathlib.Path("~{}".format(user))

        # If exists and is a directory, the parsing failed.
        self.assertFalse(f.is_file())

    def test_filepath_dir_traversal(self):
        write_to_file("/tmp/cloudmarker/../abc")
        f = pathlib.Path(os.path.join("/tmp/abc", "mock_worker.json"))
        self.assertTrue(f.is_file())

    def tearDown(self):
        # remove all junk files created after every test
        user = os.getenv("USER")
        p = [
            '/tmp/abc',
            os.path.expanduser('~/caramel_l33t'),
            os.path.expanduser('~/caramel_tpb'),
            '~{}'.format(user),
            '~',
            'test_tmp'
        ]

        for path in p:
            if pathlib.Path(path).exists():
                # delete the directory recursively
                shutil.rmtree(path)

    def test_makedirs(self):
        file_store_path = 'test_tmp'
        filestore.FileStore(path=file_store_path)
        self.assertTrue(os.path.isdir(file_store_path))

    def test_write(self):
        file_store_path = 'test_tmp'
        f = filestore.FileStore(path=file_store_path)
        records = [
            {
                'raw': {'record_type': 'alpha', 'a': 'apple'},
                'com': {'origin_worker': 'mock_worker'},
            },
            {
                'raw': {'record_type': 'alpha', 'b': 'ball'},
                'com': {'origin_worker': 'mock_worker'},
            },
            {
                'raw': {'record_type': 'alpha', 'c': 'cat'},
                'com': {'origin_worker': 'mock_worker'},
            }
        ]

        # Write the records.
        for record in records:
            f.write(record)
        f.done()

        # Read the records.
        with open(os.path.join(file_store_path, 'mock_worker.json')) as f:
            read_records = json.load(f)

        self.assertEqual(read_records, records)
