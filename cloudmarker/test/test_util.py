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

    def test_expand_port_ranges_empty_list(self):
        ports = util.expand_port_ranges([])
        self.assertEqual(ports, set())

    def test_expand_port_ranges_single_port(self):
        ports = util.expand_port_ranges(['80'])
        self.assertEqual(ports, {80})

    def test_expand_port_ranges_duplicate_ports(self):
        ports = util.expand_port_ranges(['80', '80'])
        self.assertEqual(ports, {80, 80})

    def test_expand_port_ranges_duplicate_port_numbers(self):
        ports = util.expand_port_ranges(['80', '80'])
        self.assertEqual(ports, {80, 80})

    def test_expand_port_ranges_single_range(self):
        ports = util.expand_port_ranges(['80-89'])
        self.assertEqual(ports, set(range(80, 90)))

    def test_expand_port_ranges_overlapping_ranges(self):
        ports = util.expand_port_ranges(['80-89', '85-99'])
        self.assertEqual(ports, set(range(80, 100)))

    def test_expand_port_ranges_all(self):
        ports = util.expand_port_ranges(['0-65535'])
        self.assertEqual(ports, set(range(0, 65536)))

    def test_expand_port_ranges_empty_range(self):
        ports = util.expand_port_ranges(['81-80'])
        self.assertEqual(ports, set())

    def test_expand_port_ranges_single_port_range(self):
        ports = util.expand_port_ranges(['80-80'])
        self.assertEqual(ports, {80})

    def test_expand_port_ranges_invalid_port_range(self):
        with self.assertRaises(util.PortRangeError):
            util.expand_port_ranges(['8080a'])

    def test_expand_port_ranges_invalid_port_in_port_range(self):
        with self.assertRaises(util.PortRangeError):
            util.expand_port_ranges(['8080a-8089'])

    def test_friendly_string_present(self):
        s = util.friendly_string('azure')
        self.assertEqual(s, 'Azure')

    def test_friendly_string_missing(self):
        s = util.friendly_string('foo')
        self.assertEqual(s, 'foo')

    def test_friendly_list_zero_items(self):
        s = util.friendly_list([])
        self.assertEqual(s, 'none')

    def test_friendly_list_one_item(self):
        s = util.friendly_list(['apple'])
        self.assertEqual(s, 'apple')

    def test_friendly_list_two_items(self):
        s = util.friendly_list(['apple', 'ball'])
        self.assertEqual(s, 'apple and ball')

    def test_friendly_list_three_items(self):
        s = util.friendly_list(['apple', 'ball', 'cat'])
        self.assertEqual(s, 'apple, ball, and cat')

    def test_friendly_list_two_items_conjunction(self):
        s = util.friendly_list(['apple', 'ball'], 'or')
        self.assertEqual(s, 'apple or ball')

    def test_friendly_list_three_items_conjunction(self):
        s = util.friendly_list(['apple', 'ball', 'cat'], 'or')
        self.assertEqual(s, 'apple, ball, or cat')

    def test_pluralize_zero(self):
        s = util.pluralize(0, 'apple')
        self.assertEqual(s, 'apples')

    def test_pluralize_one(self):
        s = util.pluralize(1, 'apple')
        self.assertEqual(s, 'apple')

    def test_pluralize_two(self):
        s = util.pluralize(2, 'apple')
        self.assertEqual(s, 'apples')

    def test_pluralize_zero_suffix(self):
        s = util.pluralize(0, 'potato', 'es')
        self.assertEqual(s, 'potatoes')

    def test_pluralize_one_suffix(self):
        s = util.pluralize(1, 'potato', 'es')
        self.assertEqual(s, 'potato')

    def test_pluralize_two_suffix(self):
        s = util.pluralize(2, 'potato', 'es')
        self.assertEqual(s, 'potatoes')

    def test_pluralize_zero_suffixes(self):
        s = util.pluralize(0, 'sky', 'y', 'ies')
        self.assertEqual(s, 'skies')

    def test_pluralize_one_suffixes(self):
        s = util.pluralize(1, 'sky', 'y', 'ies')
        self.assertEqual(s, 'sky')

    def test_pluralize_two_suffixes(self):
        s = util.pluralize(2, 'sky', 'y', 'ies')
        self.assertEqual(s, 'skies')

    def test_pluralize_two_surplus_suffix(self):
        with self.assertRaises(util.PluralizeError):
            util.pluralize(2, 'sky', 'y', 'ies', 'foo')
