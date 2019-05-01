"""Firewall rule event.

This module defines the :class:`FirewallRuleEvent` class that identifies
weak firewall rules. This plugin works on the firewall properties found
in the ``com`` bucket of firewall rule records.
"""


import logging

from cloudmarker import util

_log = logging.getLogger(__name__)


class FirewallRuleEvent:
    """Firewall rule event plugin."""

    def __init__(self, ports=None):
        """Create an instance of :class:`FirewallRuleEvent` plugin.

        Arguments:
            ports (list): A list of strings that represent the ports to
                be checked for insecure exposure to the Internet. If
                ``None`` is specified or if unspecified, then this
                plugin defaults to checking ports 22, 3389, 1433, 1521,
                3306, and 5432 for insecure exposure.

        """
        if ports is None:
            self._ports = {
                22,    # SSH
                3389,  # RDP
                1433,  # Microsoft SQL Server
                1521,  # Oracle DB
                3306,  # MySQL
                5432,  # Postgres
            }
        else:
            self._ports = set(ports)

    def eval(self, record):
        """Evaluate firewall rules to check for insecurely exposed ports.

        Arguments:
            record (dict): A firewall rule record.

        Yields:
            dict: An event record representing an insecurely exposed port.

        """
        # If 'com' bucket is missing, we have a malformed record. Log a
        # warning and ignore it.
        com = record.get('com')
        if com is None:
            _log.warning('Firewall rule record is missing com key: %r',
                         record)
            return

        # This plugin understands firewall rule records only, so ignore
        # any other record types.
        common_record_type = com.get('record_type')
        if common_record_type != 'firewall_rule':
            return

        # Ignore disabled firewall rule.
        if not com.get('enabled'):
            return

        # If the rule is not an ingress/inbound rule, ignore it.
        if com.get('direction') != 'in':
            return

        # If the rule is not an allow rule, ignore it.
        if com.get('access') != 'allow':
            return

        # If the rule is not a TCP port rule, ignore it.
        if com.get('protocol') not in ('tcp', 'all'):
            return

        # If the rule does not expose ports to the entire Internet,
        # ignore it.
        if '0.0.0.0/0' not in com.get('source_addresses'):
            return

        # Find the set of ports in self._ports that are exposed by the
        # firewall rule record.
        port_ranges = com.get('destination_ports')
        expanded_ports = util.expand_port_ranges(port_ranges)
        exposed_ports = self._ports.intersection(expanded_ports)

        # If there are no insecurely exposed ports, we do not need to
        # generate an event.
        if exposed_ports == set():
            return

        # Convert the set of ports to a sorted list of ports.
        exposed_ports = sorted(list(exposed_ports))

        # Human-friendly plain English description of the event along
        # with a recommendation.
        friendly_cloud_type = util.friendly_string(com.get('cloud_type'))
        port_label = util.pluralize(len(exposed_ports), 'port')
        friendly_exposed_ports = util.friendly_list(exposed_ports)
        reference = com.get('reference')
        description = (
            '{} firewall rule {} exposes {} {} to the entire Internet.'
            .format(friendly_cloud_type, reference, port_label,
                    friendly_exposed_ports)
        )
        recommendation = (
            'Check {} firewall rule {} and update rules to restrict '
            'access to {} {}.'
            .format(friendly_cloud_type, reference, port_label,
                    friendly_exposed_ports)
        )

        event_record = {
            # Preserve the extended properties from the firewall
            # rule record because they provide useful context to
            # locate the firewall rule that led to the event.
            'ext': util.merge_dicts(record.get('ext', {}), {
                'record_type': 'firewall_rule_event'
            }),

            'com': {
                'cloud_type': com.get('cloud_type'),
                'record_type': 'firewall_rule_event',
                'exposed_ports': exposed_ports,
                'reference': reference,
                'description': description,
                'recommendation': recommendation,
            }
        }

        _log.info('Generating firewall_rule_event; %r', event_record)
        yield event_record

    def done(self):
        """Perform cleanup work.

        Currently, this method does nothing. This may change in future.
        """
