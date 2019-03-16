"""Firewall Rule Event plugin for GCP Firewall rule record.

This modules define a :class:`FirewallEvent` that identifies weak Firewall
rules for Google Cloud Platform.
"""


class FirewallEvent:
    """Firewall Rule Event plugin.

    This class identifies weak Firewall rules in the record objects by
    comparing the them with predefined weak Firewall rules
    configurations.
    """

    def __init__(self):
        """Create an instance of :class:`FirewallEvent` plugin."""
        # self._rules defines the set of weak/misconfigured
        # firewall rules. Given any firewall rule, is compared with
        # these predefined weak misconfigurations if the rule matches to
        # any one predefined rule, it will be marked as weak and will be
        # reported as anomaly. Adding IPProtocol field have been skipped
        # to check for misconfiguration as GCP docs says that: The
        # protocol type is required when creating a firewall rule. This
        # value can either be one of the following well known protocol
        # strings (tcp, udp, icmp, esp, ah, ipip, sctp), or the IP
        # protocol number, implying it cannot be *.
        self._rules = {
            'sourceRanges': [
                '0.0.0.0/0',
                '*'
            ],
            'destinationRanges': [
                '0.0.0.0/0',
                '*'
            ],
        }

    def _process_rule(self, record):
        misconfigurations = []

        for weak_rule_key in self._rules:
            if weak_rule_key in record:
                for record_item in record[weak_rule_key]:
                    if (record_item in
                            self._rules[weak_rule_key]):
                        misconfigurations.append(weak_rule_key
                                                 + ':'
                                                 + record_item)
        return {
            'misconfigurations': misconfigurations,
            'id': record['id']
        }

    def eval(self, record):
        """Evaluate Firewall rules for a given record.

        Evaluate the weak security misconfigurations for each record and
        collate each weakly identified record with its misconfigurations. This
        function will only evaluate firewall_rule record.

        For each such record it will create a dict object containing the weak
        misconfigurations and return those records.

        Arguments:
            record (dict): Dictionary containing the rules definition.

        Yields:
            anomaly (dict): Dictionary representing anomaly.

        The anomaly record yielded by this method would look like:

        .. code:: python

            {
                "record_type": "firewall_alert",
                "rule": "https://www.googleapis.com/compute/v1/projects"
                        "/foo/global/firewalls/default-allow-http",
                "network":"https://www.googleapis.com/compute/v1/projects"
                          "/foo/global/networks/default",
                "misconfigurations": [
                    "sourceRanges(s):0.0.0.0/0",
                    "destinationRanges(s):0.0.0.0/0",
                ]
                "id": "7890789078907890"
            }

        """
        # Process firewall rule only if the record type is 'firewall_rule' and
        # the rule is not disabled.
        if (record['record_type'] != 'firewall_rule'
                or record['disabled']):
            return

        alert_record = {
            'record_type': 'firewall_alert',
        }

        if 'selfLink' in record.keys():
            alert_record['rule'] = record['selfLink']
        if 'network' in record.keys():
            alert_record['network'] = record['network']

        alert_record.update(self._process_rule(record))

        # if misconfigurations are not identified then dont report that
        # anomaly record
        if alert_record['misconfigurations']:
            yield alert_record

    def done(self):
        """Perform cleanup work.

        Currently, this method does nothing because there are no clean
        up tasks associated with the :class:`FirewallEvent` plugin.
        This may change in future.
        """
