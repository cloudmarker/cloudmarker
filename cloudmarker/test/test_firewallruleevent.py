"""Tests for FirewallRuleEventTest plugin."""


import copy
import unittest

from cloudmarker.events import firewallruleevent

base_record = {
    'com': {
        'record_type': 'firewall_rule',
        'enabled': True,
        'direction': 'in',
        'access': 'allow',
        'protocol': 'tcp',
        'source_addresses': ['0.0.0.0/0'],
        'destination_ports': ['0-65535'],
    }
}


class FirewallRuleEventTest(unittest.TestCase):
    """Tests for FirewallRuleEventTest plugin."""

    def test_tcp_all_exposed_ports(self):
        record = copy.deepcopy(base_record)
        plugin = firewallruleevent.FirewallRuleEvent(ports=[22, 3389])
        events = list(plugin.eval(record))
        self.assertEqual(events[0]['com']['exposed_ports'], [22, 3389])

    def test_tcp_22_exposed_ports(self):
        record = copy.deepcopy(base_record)
        record['com']['destination_ports'] = ['22']
        plugin = firewallruleevent.FirewallRuleEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events[0]['com']['exposed_ports'], [22])

    def test_tcp_no_exposed_ports(self):
        record = copy.deepcopy(base_record)
        record['com']['destination_ports'] = ['8080']
        plugin = firewallruleevent.FirewallRuleEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_com_missing(self):
        record = {}
        plugin = firewallruleevent.FirewallRuleEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_not_firewall_rule(self):
        record = copy.deepcopy(base_record)
        record['com']['record_type'] = 'foo'
        plugin = firewallruleevent.FirewallRuleEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_not_enabled(self):
        record = copy.deepcopy(base_record)
        record['com']['enabled'] = False
        plugin = firewallruleevent.FirewallRuleEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_direction_not_in(self):
        record = copy.deepcopy(base_record)
        record['com']['direction'] = 'out'
        plugin = firewallruleevent.FirewallRuleEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_access_not_allow(self):
        record = copy.deepcopy(base_record)
        record['com']['access'] = 'deny'
        plugin = firewallruleevent.FirewallRuleEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_protocol_not_tcp(self):
        record = copy.deepcopy(base_record)
        record['com']['protocol'] = 'udp'
        plugin = firewallruleevent.FirewallRuleEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_protocol_all(self):
        record = copy.deepcopy(base_record)
        record['com']['protocol'] = 'all'
        plugin = firewallruleevent.FirewallRuleEvent(ports=[22, 3389])
        events = list(plugin.eval(record))
        self.assertEqual(events[0]['com']['exposed_ports'], [22, 3389])

    def test_source_addresses_not_entire_internet(self):
        record = copy.deepcopy(base_record)
        record['com']['source_addresses'] = ['4.0.0.0/8']
        plugin = firewallruleevent.FirewallRuleEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events, [])

    def test_cloud_type(self):
        record = copy.deepcopy(base_record)
        record['com']['cloud_type'] = 'azure'
        plugin = firewallruleevent.FirewallRuleEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events[0]['com']['cloud_type'], 'azure')

    def test_record_type(self):
        record = copy.deepcopy(base_record)
        plugin = firewallruleevent.FirewallRuleEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events[0]['com']['record_type'],
                         'firewall_rule_event')

    def test_reference(self):
        record = copy.deepcopy(base_record)
        record['com']['reference'] = 'foo_ref'
        plugin = firewallruleevent.FirewallRuleEvent()
        events = list(plugin.eval(record))
        self.assertEqual(events[0]['com']['reference'], 'foo_ref')

    def test_ext_copied_to_event(self):
        record = copy.deepcopy(base_record)
        record['ext'] = {'a': 'apple', 'b': 'ball', 'record_type': 'foo'}
        plugin = firewallruleevent.FirewallRuleEvent()
        events = list(plugin.eval(record))
        expected_ext = {
            'a': 'apple',
            'b': 'ball',
            'record_type': 'firewall_rule_event',
        }
        self.assertEqual(events[0]['ext'], expected_ext)

    def test_ext_unaltered_in_original_record(self):
        record = copy.deepcopy(base_record)
        record['ext'] = {'a': 'apple', 'b': 'ball', 'record_type': 'foo'}
        plugin = firewallruleevent.FirewallRuleEvent()
        expected_ext = {
            'a': 'apple',
            'b': 'ball',
            'record_type': 'foo',
        }
        events = list(plugin.eval(record))
        self.assertEqual(len(events), 1)
        self.assertEqual(record['ext'], expected_ext)
