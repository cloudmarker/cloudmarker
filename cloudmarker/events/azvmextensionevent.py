"""Microsoft Azure VM extension event.

This module defines the :class:`AzVMExtensionEvent` class that
evaluates Azure VM extensions. This plugin works on the virtual
machine properties found in the ``ext`` bucket of ``vm_instance_view``
records.
"""


import logging

from cloudmarker import util

_log = logging.getLogger(__name__)


class AzVMExtensionEvent:
    """Az VM Data extension event plugin."""

    def __init__(self, whitelisted=None, blacklisted=None, required=None):
        """Create an instance of :class:`AzVMExtensionEvent`.

        Arguments:
            whitelisted (list): List of whitelisted extensions.
            blacklisted (list): List of blacklisted extensions.
            required (list): List of required extensions.

        """
        if whitelisted is None:
            whitelisted = []
        if blacklisted is None:
            blacklisted = []
        if required is None:
            required = []
        self._whitelisted = whitelisted
        self._blacklisted = blacklisted
        self._required = required

    def eval(self, record):
        """Evaluate Azure virtual machine for extensions.

        Arguments:
            record (dict): A virtual machine record.

        Yields:
            dict: An event record representing an Azure VM with
            misconfigured extensions

        """
        com = record.get('com', {})
        if com is None:
            return

        if com.get('cloud_type') != 'azure':
            return

        ext = record.get('ext', {})
        if ext is None:
            return

        if ext.get('record_type') != 'vm_instance_view':
            return

        extensions = ext.get('extensions')

        added_extensions = set(extensions)

        if self._blacklisted:
            added_blacklisted_ext = list(set(self._blacklisted) &
                                         added_extensions)
            yield from _get_azure_vm_blacklisted_extension_event(
                com, ext, added_blacklisted_ext)

        if self._whitelisted:
            added_unapproved_ext = list(added_extensions -
                                        (set(self._whitelisted) -
                                         set(self._blacklisted)))
            yield from _get_azure_vm_unapproved_extension_event(
                com, ext, added_unapproved_ext)

        if self._required:
            missing_required_ext = list((set(self._required) -
                                         set(self._blacklisted)) -
                                        added_extensions)
            yield from _get_azure_vm_required_extension_event(
                com, ext, missing_required_ext)

    def done(self):
        """Perform cleanup work.

        Currently, this method does nothing. This may change in future.
        """


def _get_azure_vm_blacklisted_extension_event(com, ext, blacklisted):
    """Evaluate Azure VM for blacklisted extensions.

    Arguments:
        com (dict): Virtual machine record `com` bucket
        ext (dict): Virtual machine record `ext` bucket
        blacklisted (list): Added blacklisted extension list
    Returns:
        dict: An event record representing VM with blacklisted extenstions

    """
    if not blacklisted:
        return
    friendly_cloud_type = util.friendly_string(com.get('cloud_type'))
    reference = com.get('reference')
    description = (
        '{} virtual machine {} has blacklisted extensions {}'
        .format(friendly_cloud_type, reference,
                util.friendly_list(blacklisted))
    )
    recommendation = (
        'Check {} virtual machine {} and remove blacklisted extensions {}'
        .format(friendly_cloud_type, reference,
                util.friendly_list(blacklisted))
    )

    event_record = {
        # Preserve the extended properties from the virtual
        # machine record because they provide useful context to
        # locate the virtual machine that led to the event.
        'ext': util.merge_dicts(ext, {
            'record_type': 'vm_blacklisted_extension_event'
        }),
        'com': {
            'cloud_type': com.get('cloud_type'),
            'record_type': 'vm_blacklisted_extension_event',
            'reference': reference,
            'description': description,
            'recommendation': recommendation,
        }
    }

    _log.info('Generating vm_blacklisted_extension_event; %r', event_record)
    yield event_record


def _get_azure_vm_unapproved_extension_event(com, ext, not_whitelisted):
    """Evaluate Azure VM for unapproved extensions.

    Arguments:
        com (dict): Virtual machine record `com` bucket
        ext (dict): Virtual machine record `ext` bucket
        not_whitelisted (list): Not whitelisted extension list
    Returns:
        dict: An event record representing VM with unapproved extenstions

    """
    if not not_whitelisted:
        return
    friendly_cloud_type = util.friendly_string(com.get('cloud_type'))
    reference = com.get('reference')
    description = (
        '{} virtual machine {} has unapproved extensions {}'
        .format(friendly_cloud_type, reference,
                util.friendly_list(not_whitelisted))
    )
    recommendation = (
        'Check {} virtual machine {} and remove unapproved extensions {}'
        .format(friendly_cloud_type, reference,
                util.friendly_list(not_whitelisted))
    )

    event_record = {
        # Preserve the extended properties from the virtual
        # machine record because they provide useful context to
        # locate the virtual machine that led to the event.
        'ext': util.merge_dicts(ext, {
            'record_type': 'vm_unapproved_extension_event'
        }),
        'com': {
            'cloud_type': com.get('cloud_type'),
            'record_type': 'vm_unapproved_extension_event',
            'reference': reference,
            'description': description,
            'recommendation': recommendation,
        }
    }

    _log.info('Generating vm_unapproved_extension_event; %r', event_record)
    yield event_record


def _get_azure_vm_required_extension_event(com, ext, missing_required):
    """Evaluate Azure VM for unapproved extensions.

    Arguments:
        com (dict): Virtual machine record `com` bucket
        ext (dict): Virtual machine record `ext` bucket
        missing_required (list): Missing required extension list
    Returns:
        dict: An event record representing VM with unapproved extenstions

    """
    if not missing_required:
        return
    friendly_cloud_type = util.friendly_string(com.get('cloud_type'))
    reference = com.get('reference')
    description = (
        '{} virtual machine {} is missing required extensions {}'
        .format(friendly_cloud_type, reference,
                util.friendly_list(missing_required))
    )
    recommendation = (
        'Check {} virtual machine {} and add required extensions {}'
        .format(friendly_cloud_type, reference,
                util.friendly_list(missing_required))
    )

    event_record = {
        # Preserve the extended properties from the virtual
        # machine record because they provide useful context to
        # locate the virtual machine that led to the event.
        'ext': util.merge_dicts(ext, {
            'record_type': 'vm_required_extension_event'
        }),
        'com': {
            'cloud_type': com.get('cloud_type'),
            'record_type': 'vm_required_extension_event',
            'reference': reference,
            'description': description,
            'recommendation': recommendation,
        }
    }

    _log.info('Generating vm_required_extension_event; %r', event_record)
    yield event_record
