"""IAM-Policy rule event.

This module defines the :class:`GCPIAMCorpRuleEvent` class that identifies
weak IAM-Policy related rules. This plugin works on the GCP IAM properties
found in the ``com`` bucket of IAM-Policy rule records.
"""


import logging

from cloudmarker import util

_log = logging.getLogger(__name__)


class GCPIAMCorpRuleEvent:
    """IAM-Policy rule event plugin."""

    def __init__(self):
        """Create an instance of :class:`GCPIAMCorpRuleEvent` plugin."""

    def eval(self, record):
        """Evaluate IAM rules to check corporate login credentials.

        Arguments:
            record (dict): A IAM-Corp-Login-Policy rule record.

        Yields:
            dict: An event record representing a personal Gmail accounts.

        """
        # If 'com' bucket is missing, we have a malformed record. Log a
        # warning and ignore it.
        com = record.get('com')
        if com is None:
            _log.warning('IAM-Policy rule record is missing com key: %r',
                         record)
            return

        # This plugin understands IAM-Policy rule records only, so ignore
        # any other record types.
        common_record_type = com.get('record_type')
        if common_record_type != 'iam_corp_login_policy_rule':
            return

        members = record['raw']['members']
        personal_account = None
        for member in members:
            if 'user' in member:
                user = member.split('user:')
                if user[1].endswith('gmail.com'):
                    personal_account = user[1]
                    reference = com.get('reference')
                    description = (
                        'Personal gmail account {} has been used.'
                        .format(personal_account)
                    )
                    recommendation = (
                        'Ensure that corporate login credentials are used instead of Gmail accounts.'
                    )

                    event_record = {
                        'ext': util.merge_dicts(record.get('ext', {}), {
                            'record_type': 'iam-policy-corp-login-rule-event'
                        }),

                        'com': {
                            'cloud_type': com.get('cloud_type'),
                            'record_type': 'iam-policy-corp-login-rule-event',
                            'reference': reference,
                            'description': description,
                            'recommendation': recommendation,
                        }
                    }
                    _log.info('Generating iam_policy_rule; %r', event_record)
                    yield event_record

    def done(self):
        """Perform cleanup work.

        Currently, this method does nothing. This may change in future.
        """
