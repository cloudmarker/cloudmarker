"""Tests for MongoDB store plugin."""


import unittest
from collections import defaultdict

from pymongo import MongoClient

from cloudmarker.stores import mongodbstore


class DummyModel:
    """A DummyModel to demonstrate constraint validation."""

    __COLLECTION__ = "test_collection"
    __ENFORCE__ = "error"  # ["error", "warn"]
    __VALIDATOR__ = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["name"],
            "properties": {
                "name": {
                    "bsonType": "string",
                    "minLength": 3,
                    "maxLength": 63,
                    "description": "Name of the user, 2 < length < 64,required"
                }
            }
        }
    }

    def __init__(self, name="", attr=defaultdict()):
        """Initialize the DummyModel object for test."""
        self.name = name
        self.attr = attr

    @staticmethod
    def validator():
        return DummyModel.__VALIDATOR__

    @staticmethod
    def enforce():
        return DummyModel.__ENFORCE__

    @staticmethod
    def collection():
        return DummyModel.__COLLECTION__

    def marshal(self):
        mp = {
            "name": self.name
        }

        for k, v in self.attr.items():
            mp[k] = v

        mp["record_type"] = DummyModel.collection()

        return mp


class MongoDBStoreTest(unittest.TestCase):
    """Tests for MongoDB store plugin.

    All tests would require a running instance of mongoDB. You may use
    the docker compose file in ``cloudmarker/test/data/docker-comppose.yml``
    $ docker-compute -f cloudmarker/test/data/docker-comppose.yml up
    """

    def test_connection(self):
        client = MongoClient(host='localhost', port=27017,
                             username='dummy', password='password')

        db = client["test"]

        for collection in db.list_collection_names():
            db[collection].drop()

        store = mongodbstore.MongoDBStore('test', 'dummy',
                                          'password', 'localhost')
        compute = {
            "record_type": "compute",
            "id": "sample/compute/compute_1",
            "compute_name": "testing",
            "machine_size": "MX",
            "provisioning_state": "done"
        }

        nic = {
            "record_type": "nic",
            "compute_id": "sample/compute/compute_1",
            "id": "sample/compute/nic_2",
            "mac": "aa:aa:aa:aa:aa:aa",
            "provisioning_state": "done",
            "ip": [
                {
                    "id": "sample/compute/nic_2/ip_1",
                    "primary": True,
                    "private_ip": "10.0.0.1",
                    "private_ip_version": "IPv4",
                    "private_ip_allocation": "dynamic",
                    "public_ip": "123.123.123.123"
                },
                {
                    "id": "sample/compute/nic_2/ip_2",
                    "primary": False,
                    "private_ip": "10.0.0.2",
                    "private_ip_version": "IPv4",
                    "private_ip_allocation": "dynamic"
                }
            ]
        }

        store.write(compute)
        store.write(nic)

        store.done()

        self.assertEqual(db['compute'].count_documents({}), 1)
        self.assertEqual(db['nic'].count_documents({}), 1)

    def test_valid_insert(self):
        client = MongoClient(host='localhost', port=27017,
                             username='dummy', password='password')

        db = client["test"]

        for collection in db.list_collection_names():
            db[collection].drop()

        store = mongodbstore.MongoDBStore('test', 'dummy', 'password',
                                          'localhost', 27017,
                                          models=[DummyModel])
        # valid insert
        m = {
            "record_type": DummyModel.collection(),
            "name": "Cooper Gatlin",
            "age": 25
        }

        store.write(m)
        store.done()

        self.assertEqual(db[DummyModel.collection()].count_documents({}), 1)

    def test_failed_insert(self):
        client = MongoClient(host='localhost', port=27017,
                             username='dummy', password='password')

        db = client["test"]

        for collection in db.list_collection_names():
            db[collection].drop()

        store = mongodbstore.MongoDBStore('test', 'dummy', 'password',
                                          'localhost', 27017,
                                          models=[DummyModel])
        # invalid insert
        m_invalid = {
            "record_type": DummyModel.collection(),
            "name": "zz",
            "age": 25
        }
        m_valid = DummyModel("Cooper Gatlin", {"age": 25}).marshal()

        store.write(m_invalid)
        store.write(m_valid)
        store.done()

        # Testing if atleast the valid record is inserted. This is enforced
        # by the option ordered=False in insert_many, that tries to insert all
        # documents unordered. Since mongo already validates all docsuments
        # it makes sense to try to insert all, the failed ones will be rejected
        # Check http://api.mongodb.com/python/current/api/pymongo/
        # collection.html#pymongo.collection.Collection.insert_many
        self.assertEqual(db[DummyModel.collection()].count_documents({}), 1)

    def test_warning_insert(self):
        client = MongoClient(host='localhost', port=27017,
                             username='dummy', password='password')

        db = client["test"]

        for collection in db.list_collection_names():
            db[collection].drop()

        store = mongodbstore.MongoDBStore('test', 'dummy', 'password',
                                          'localhost', 27017,
                                          models=[DummyModel])
        # valid insert
        m = {
            "record_type": DummyModel.collection(),
            "name": "zz",
            "age": 25
        }

        db.command({
            "collMod": DummyModel.collection(),
            "validationAction": "warn"
        })

        store.write(m)
        store.done()

        self.assertEqual(db[DummyModel.collection()].count_documents({}), 1)
