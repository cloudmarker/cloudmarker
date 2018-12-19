"""Tests for util module."""

import os
import unittest

from cloudmarker import util
from cloudmarker.test import data_path


class MockPlugin():
    """A mock plugin to test plugin loading."""

    def __init__(self, a=1, b=2):
        """Mock initializer."""
        self.a = a
        self.b = b


class UtilTest(unittest.TestCase):
    """Tests for util module."""

    def test_load_config(self):
        path1 = os.path.join(data_path, 'config1.yaml')
        path2 = os.path.join(data_path, 'config2.yaml')
        path3 = os.path.join(data_path, 'missing.yaml')
        config = util.load_config([path1, path2, path3])
        self.assertEqual(config, {'foo': 'bar', 'baz': 'qux'})

    def test_load_plugin_syntax_error(self):
        with self.assertRaises(util.PluginError):
            util.load_plugin({'plugin': 'foo'})

    def test_load_plugin_missing_error(self):
        plugin_config = {
            'plugin': 'cloudmarker.test.test_util.MissingPlugin'
        }
        with self.assertRaises(AttributeError):
            util.load_plugin(plugin_config)

    def test_load_plugin_without_params(self):
        plugin_config = {
            'plugin': 'cloudmarker.test.test_util.MockPlugin'
        }
        plugin = util.load_plugin(plugin_config)
        self.assertIsInstance(plugin, MockPlugin)
        self.assertEqual(plugin.a, 1)
        self.assertEqual(plugin.b, 2)

    def test_load_plugin_with_params(self):
        plugin_config = {
            'plugin': 'cloudmarker.test.test_util.MockPlugin',
            'params': {
                'a': 3,
                'b': 4,
            }
        }
        plugin = util.load_plugin(plugin_config)
        self.assertIsInstance(plugin, MockPlugin)
        self.assertEqual(plugin.a, 3)
        self.assertEqual(plugin.b, 4)

    def test_parse_cli_args_none(self):
        args = util.parse_cli([])
        self.assertEqual(args.config, ['config.base.yaml', 'config.yaml'])

    def test_parse_cli_args_config(self):
        # Short option.
        args = util.parse_cli(['-c', 'foo.yaml', 'bar.yaml'])
        self.assertEqual(args.config, ['foo.yaml', 'bar.yaml'])
        # Long option.
        args = util.parse_cli(['--config', 'baz.yaml', 'qux.yaml'])
        self.assertEqual(args.config, ['baz.yaml', 'qux.yaml'])

    def test_merge_dicts_simple(self):
        a = {'a': 1, 'b': 2}
        b = {'b': 3, 'c': 4}
        c = util.merge_dicts(a, b)
        self.assertEqual(c, {'a': 1, 'b': 3, 'c': 4})

    def test_merge_dicts_nested(self):
        a = {'a': 1, 'b': {'c': 2, 'd': 3}}
        b = {'a': 1, 'b': {'d': 4, 'e': 5}}
        c = util.merge_dicts(a, b)
        self.assertEqual(c, {'a': 1, 'b': {'c': 2, 'd': 4, 'e': 5}})

    def test_merge_first_dict_empty(self):
        a = {}
        b = {'a': 1}
        c = util.merge_dicts(a, b)
        self.assertEqual(c, {'a': 1})

    def test_merge_second_dict_empty(self):
        a = {'a': 1}
        b = {}
        c = util.merge_dicts(a, b)
        self.assertEqual(c, {'a': 1})

    def test_merge_dicts_immutability_simple(self):
        a = {'a': 1}
        b = {'b': 2}
        c = util.merge_dicts(a, b)
        c['c'] = 3
        self.assertEqual(a, {'a': 1})
        self.assertEqual(b, {'b': 2})

    def test_merge_dicts_immutability_nested(self):
        a = {'a': [1, 2, 3]}
        b = {'a': [4, 5, 6]}
        c = util.merge_dicts(a, b)
        c['a'].append(7)
        self.assertEqual(a, {'a': [1, 2, 3]})
        self.assertEqual(b, {'a': [4, 5, 6]})
