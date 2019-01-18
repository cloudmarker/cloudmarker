"""Tests for filestore plugin."""


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
        "record_type": "dummy",
        "data": {
            "test_name": "tilde_filename"
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

        f = pathlib.Path(os.path.join("/tmp/abc", "dummy.json"))
        self.assertTrue(f.is_file())

    def tearDown(self):
        # remove all junk files created after every test
        user = os.getenv("USER")
        p = [
            "/tmp/abc",
            os.path.expanduser("~/caramel_l33t"),
            os.path.expanduser("~/caramel_tpb"),
            "~{}".format(user),
            "~"
        ]

        for path in p:
            if pathlib.Path(path).exists():
                # delete the directory recursively
                shutil.rmtree(path)
