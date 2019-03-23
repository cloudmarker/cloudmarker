"""Tests for Firewall Event Plugin."""

import copy
import unittest

from cloudmarker.events import firewallevent

mock_firewall_record = {
    'kind': 'compute#firewall',
    'id': '7890789078907890',
    'creationTimestamp': '2018-12-19T01:43:51.988-08:00',
    'name': 'default-allow-ssh',
    'description': 'str',
    'network': 'https://www.googleapis.com/compute/v1/'
               'projects/foo/global/networks/default',
    'priority': 1000,
    'sourceRanges': [
        '0.0.0.0/0'
    ],
    'targetTags': [
        'https-server'
    ],
    'allowed': [
        {
            'IPProtocol': 'tcp',
            'ports': [
                '80',
                '8080-8090'
            ]
        }
    ],
    'direction': 'INGRESS',
    'logConfig': {
        'enable': True
    },
    'disabled': False,
    'selfLink': 'https://www.googleapis.com/compute/v1/'
                'projects/foo/global/firewalls/default-allow-https',
    'record_type': 'firewall_rule'
}

# mock_alert_record should be same as alert record generated when
# mock_firewall_record is passed to `firewallevent.FirewallEvent.eval()`
mock_alert_record = [
    {
        'record_type': 'firewall_alert',
        'rule': 'https://www.googleapis.com/compute/v1/projects/foo/'
                'global/firewalls/default-allow-https',
        'network': 'https://www.googleapis.com/compute/v1/projects/foo'
                   '/global/networks/default',
        'misconfigurations': ['sourceRanges:0.0.0.0/0'],
        'id': '7890789078907890'
    }
]


class FirewallEventTest(unittest.TestCase):
    """Testcases for Firewall Event plugins."""

    def test_firewallevent_eval_non_firewall_record(self):
        firewall_record_data = copy.deepcopy(mock_firewall_record)
        # Firewall event shuold not process the rule if the record_type is foo
        firewall_record_data.update({'record_type': 'foo'})

        fwevent = firewallevent.FirewallEvent()

        alert_record = list(fwevent.eval(firewall_record_data))

        # In case of non firewall record, FirewallEvent.eval should return
        # empty list.
        self.assertListEqual(alert_record, [])

    def test_firewallevent_eval_firewall_record(self):
        firewall_record_data = copy.deepcopy(mock_firewall_record)

        fwevent = firewallevent.FirewallEvent()

        alert_record = list(fwevent.eval(firewall_record_data))

        # In case the firewall_record_data with record_type is firewall_rule is
        # evaluated then the yielded value should match mock_alert_record.
        self.assertListEqual(alert_record, mock_alert_record)
