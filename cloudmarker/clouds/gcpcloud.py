"""Google Cloud Platform (GCP) plugin to read GCP infrastructure data.

This module defines the :class:`GCPCloud` class that retrieves data from
Google Cloud Platform.
"""


import json
import logging

from google.oauth2 import service_account
from googleapiclient import discovery

from cloudmarker import util

_GCP_SCOPES = ['https://www.googleapis.com/auth/compute.readonly']
"""OAuth 2.0 scopes for Google APIs required by this plugin.

See https://developers.google.com/identity/protocols/googlescopes for
more details on OAuth 2.0 scopes for Google APIs."""


_log = logging.getLogger(__name__)


class GCPCloud:
    """GCP cloud plugin."""

    def __init__(self, key_file_path, zone):
        """Create an instance of :class:`GCPCloud` plugin.

        Arguments:
            key_file_path (str): Path of the service account
                key file for a project.
            zone (str): Zone of GCP Project, e.g., ``us-east1-b``.
        """
        self._key_file_path = key_file_path
        self._zone = zone

        # Service account key file also has the project name under the key
        # project_id. We will use this key file to get the project name for
        # this request.
        with open(self._key_file_path) as f:
            self._project_name = json.loads(f.read())['project_id']

        # Generating scoped credentials which will be required by the
        # discovery.build to create a resource object which we will use to
        # communicate with the API.
        credentials = service_account.Credentials
        self._credentials = credentials.from_service_account_file(
            self._key_file_path,
            scopes=_GCP_SCOPES)

        # Currently generating scoped resources with googleapiclient, requires
        # service_name and version information, the more complete information
        # about available_service name and their corresponding version is
        # located at
        # https://developers.google.com/api-client-library/python/apis/
        self._compute_resource = self._get_resource('compute', 'v1')

    def _get_resource(self, service_name, version='v1'):
        """Create a ``Resource`` object for interacting with Google APIs.

        Arguments:
            service_name (str): Name of the service of resource object.
            version (str): Version of the API for resource object.

        Returns:
            googleapiclient.discovery.Resource: Resource object for
                interacting with Google APIs.

        """
        # cache_discovery is boolean keyword argument that tells builder
        # whether or not to cache the discovery doc.
        return discovery.build(service_name,
                               version,
                               credentials=self._credentials,
                               cache_discovery=False)

    def _get_firewalls(self):
        """Query the compute resource and return firewall rules.

        Returns:
            list: A list of :obj:`dict` objects where each :obj:`dict`
                object contains a firewall rule.

        """
        # Get firewall resource from the compute resource
        firewall_resource = self._compute_resource.firewalls()

        firewall_rules = []
        next_page_token = None

        while True:
            # Prepare the request to get the list of all firewall rules for a
            # project and execute that request.
            firewall_rules_object = firewall_resource.list(
                project=self._project_name,
                pageToken=next_page_token).execute()

            firewall_rules.extend(firewall_rules_object['items'])

            # firewall_rules_object will only contain the maximum number of
            # results per page which is specified in options keyword argument
            # maxResults in list() API call. The default value of maxResults is
            # 500, if the result contains more than 500 records, nextPageToken
            # is present in response whose value is to be used to make the
            # subsequent list() call.
            if 'nextPageToken' not in firewall_rules_object.keys():
                break

            next_page_token = firewall_rules_object['nextPageToken']

        return firewall_rules

    def _get_instances(self):
        """Query the compute resource and returns instance list.

        Returns:
            list: A list of :obj:`dict` objects where each :obj:`dict`
                object contains details of a virtual machine instance.

        """
        # Get instance resource to get the list of instances for a project and
        # execute that request.
        instance_resource = self._compute_resource.instances()
        instances = []
        next_page_token = None

        while True:
            # Prepare the request to get the list of all VM instances for a
            # project and execute that request.
            instances_object = instance_resource.list(
                project=self._project_name,
                pageToken=next_page_token,
                zone=self._zone).execute()

            instances.extend(instances_object['items'])

            # instances_object will only contain the maximum number of results
            # per page which is specified in options keyword argument
            # maxResults in list() API call. The default value of maxResults is
            # 500, if the result contains more than 500 records, nextPageToken
            # key is present in response whose value is to be used to make the
            # subsequent list() call.
            if 'nextPageToken' not in instances_object.keys():
                break

            next_page_token = instances_object['nextPageToken']

        return instances

    def read(self):
        """Return a GCP infrastructure configuration record.

        Yields:
            dict: Firewall rule or VM instance configuration data.

        """
        firewalls = self._get_firewalls()
        instances = self._get_instances()

        _log.info('Found %d firewall records for project %s',
                  len(firewalls), self._project_name)
        _log.info('Found %d instances for project %s',
                  len(instances), self._project_name)

        for firewall in firewalls:
            record = {
                'raw': firewall,
                'ext': {
                    'cloud_type': 'gcp',
                    'record_type': 'firewall'
                },
                'com': {
                    'cloud_type': 'gcp',
                    'record_type': None,
                }
            }
            yield record
            yield from _get_normalized_firewall_rules(record)

        for instance in instances:
            record = {
                'raw': instance,
                'ext': {
                    'record_type': 'compute'
                },
                'com': {
                    'cloud_type': 'gcp',
                    'record_type': 'compute'
                }
            }
            yield record

    def done(self):
        """Perform clean up tasks.

        Currently, this method does nothing because there are no clean
        up tasks associated with the :class:`GCPCloud` plugin. This
        may change in future.
        """


def _get_normalized_firewall_rules(firewall_record):
    """Split a firewall record into multiple firewall rules.

    A firewall record in GCP has a top-level key named either
    ``allowed`` or ``denied``. The value of this key is a list of
    allowed or denied rules. Each such rule contains the name of allowed
    or denied protocol along with a list of allowed or denied port
    ranges.

    In order to make it easier to write event plugins to detect security
    issues in firewall, we generate a new firewall rule record for each
    allowed or denied rule we find in the value of ``allowed`` or
    ``denied`` keys in a firewall record.

    Arguments:
        firewall_record (dict): Firewall record generated by this plugin.

    Yield:
        dict: A normalized firewall rule record with ``com`` bucket
            populated with firewall rule properties in common notation.

    """
    allow_rules = firewall_record.get('raw', {}).get('allowed')
    if allow_rules is not None:
        for rule in allow_rules:
            firewall_rule = _get_normalized_firewall_rule(firewall_record,
                                                          rule)
            firewall_rule['com']['access'] = 'allow'
            yield firewall_rule

    deny_rules = firewall_record.get('raw', {}).get('denied')
    if deny_rules is not None:
        for rule in deny_rules:
            firewall_rule = _get_normalized_firewall_rule(firewall_record,
                                                          rule)
            firewall_rule['com']['access'] = 'deny'
            yield firewall_rule


def _get_normalized_firewall_rule(firewall_record, rule):
    """Create a normalized firewall rule record.

    Arguments:
        firewall_record (dict): Firewall record generated by this plugin.
        rule (dict): Raw allowed or denied rule in ``firewall``.

    Returns:
        dict: A normalized firewall rule record with ``com`` bucket
            populated with firewall rule properties in common notation.

    """
    raw_firewall = firewall_record.get('raw', {})
    record = {
        'raw': rule,

        # Preserve the extended properties from firewall record.
        'ext': util.merge_dicts(firewall_record.get('ext'), {

            # Set extended properties specific to a firewall rule.
            'record_type': 'firewall_rule',
            'firewall_id': raw_firewall.get('id'),
            'firewall_link': raw_firewall.get('selfLink'),
        }),

        'com': {
            'cloud_type': 'gcp',
            'record_type': 'firewall_rule',
            'reference': raw_firewall.get('selfLink'),

            'enabled': not raw_firewall.get('disabled'),

            'direction':
                _get_normalized_firewall_direction(raw_firewall),

            'source_addresses': raw_firewall.get('sourceRanges'),

            'protocol':
                _get_normalized_firewall_protocol(rule),

            # If the 'ports' key is missing in an allowed/denied rule,
            # it means all ports are allowed/denied.
            'destination_ports': rule.get('ports', ['0-65535'])
        }
    }
    return record


def _get_normalized_firewall_direction(firewall):
    rule_name = firewall.get('name')
    direction = firewall.get('direction')

    if direction is None:
        _log.warning('Found firewall rule without direction; name: %s',
                     rule_name)
        return None

    direction = direction.lower()

    if direction == 'ingress':
        return 'in'

    if direction == 'egress':
        return 'out'

    _log.warning('Found unknown direction in firewall rule; '
                 'direction: %s; name: %s', direction, rule_name)
    return direction


def _get_normalized_firewall_protocol(firewall_rule):
    rule_name = firewall_rule.get('name')
    protocol = firewall_rule.get('IPProtocol')

    if protocol is None:
        _log.warning('Found firewall rule without IPProtocol; name: %s',
                     rule_name)
        return None

    return protocol.lower()
