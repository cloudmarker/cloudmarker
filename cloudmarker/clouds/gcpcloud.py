"""Google Cloud Platform (GCP) plugin to read GCP infrastructure data.

This module defines the :class:`GCPCloud` class that retrieves data from
Google Cloud Platform.
"""

import json
import logging

from google.oauth2 import service_account
from googleapiclient import discovery

from cloudmarker import ioworkers, util

_GCP_SCOPES = ['https://www.googleapis.com/auth/compute.readonly',
               'https://www.googleapis.com/auth/cloud-platform.read-only']
"""OAuth 2.0 scopes for Google APIs required by this plugin.

See https://developers.google.com/identity/protocols/googlescopes for
more details on OAuth 2.0 scopes for Google APIs."""


_log = logging.getLogger(__name__)


class GCPCloud:
    """GCP cloud plugin."""

    def __init__(self, key_file_path, processes=4, threads=30,
                 _max_projects=0):
        """Create an instance of :class:`GCPCloud` plugin.

         Note: The ``_max_projects`` argument should be used only in the
         development-test-debug phase. It should not be used in
         production environment. This is why we use the convention of
         beginning it's name with underscore.

        Arguments:
            key_file_path (str): Path of the service account
                key file for a project.
            processes (int): Number of processes to launch.
            threads (int): Number of threads to launch in each process.
            _max_projects (int): Maximum number of projects to fetch
                data for if the value is greater than 0.

        """
        self._key_file_path = key_file_path
        self._processes = processes
        self._threads = threads
        self._max_projects = _max_projects

        # Service account key file also has the client email under the key
        # client_email. We will use this key file to get the client email for
        # this request.
        try:
            with open(self._key_file_path) as f:
                self._client_email = json.loads(f.read()).get('client_email')
        except OSError as e:
            self._client_email = '<unknown>'
            _log.error('Failed to read client_email from key file: %s; '
                       'error: %s: %s', self._key_file_path,
                       type(e).__name__, e)

        _log.info('Initialized; key_file_path: %s; processes: %s; threads: %s',
                  self._key_file_path, self._processes, self._threads)

    def read(self):
        """Return a GCP cloud infrastructure configuration record.

        Yields:
            dict: A GCP cloud infrastructure configuration record.

        """
        yield from ioworkers.run(self._get_projects,
                                 self._get_resources,
                                 self._processes,
                                 self._threads,
                                 __name__)

    def _build_resource(self, service_name, version='v1'):
        """Create a ``Resource`` object for interacting with Google APIs.

        Arguments:
            service_name (str): Name of the service of resource object.
            version (str): Version of the API for resource object.

        Returns:
            googleapiclient.discovery.Resource: Resource object for
                interacting with Google APIs.

        """
        credential = service_account.Credentials.from_service_account_file(
            self._key_file_path,
            scopes=_GCP_SCOPES)
        return discovery.build(service_name,
                               version,
                               credentials=credential,
                               cache_discovery=False)

    def _get_projects(self):
        """Generate tuples of record types and projects.

        The yielded tuples when unpacked would become arguments for
        :meth:`_get_resources`. Each such tuple represents a single unit
        of work that :meth:`_get_resources` can work on independently in
        its own worker thread.

        Yields:
            tuple: A tuple which when unpacked forms valid arguments for
                :meth:`_get_resources`.

        """
        try:
            cloud_resource = self._build_resource('cloudresourcemanager', 'v1')
            compute_resource = self._build_resource('compute', 'v1')

            projects = _get_resource_iterator(cloud_resource.projects(),
                                              'projects', self._key_file_path)

            for project_index, project in enumerate(projects):
                project_id = project.get('projectId')

                _log.info('Found %s',
                          util.outline_gcp_project(project_index, project,
                                                   None, self._key_file_path))

                yield ('firewall', project_index, project)

                zones = _get_resource_iterator(compute_resource.zones(),
                                               'items', self._key_file_path,
                                               project=project_id)

                for zone in zones:
                    yield ('instance', project_index, project,
                           zone.get('name'))

                if project_index + 1 == self._max_projects:
                    _log.info('Stopping projects fetch due to '
                              '_max_projects: %d; key_file_path: %s',
                              self._max_projects, self._key_file_path)
                    break

        except Exception as e:
            _log.error('Failed to fetch projects; key_file_path: %s; '
                       'error: %s: %s', self._key_file_path,
                       type(e).__name__, e)

    def _get_resources(self, record_type, project_index, project, zone=None):
        """Return a GCP infrastructure configuration record.

        Arguments:
            record_type (str): Type of record whose details have to be fetched
                from GCP.
            project_index (int): Project index
            project (Resource): GCP Resource object of the project.
            zone (str): Name of the zone for the project.

        Yields:
            dict: Firewall rule or VM instance configuration data.

        """
        _log.info('Working on %s list; %s', record_type,
                  util.outline_gcp_project(project_index, project, zone,
                                           self._key_file_path))

        project_id = project.get('projectId')
        try:
            if record_type == 'firewall':
                resource = self._build_resource('compute', 'v1')
                iterator = _get_resource_iterator(resource.firewalls(),
                                                  'items', self._key_file_path,
                                                  project=project_id)

            elif record_type == 'instance':
                resource = self._build_resource('compute', 'v1')
                iterator = _get_resource_iterator(resource.instances(),
                                                  'items', self._key_file_path,
                                                  project=project_id,
                                                  zone=zone)
            else:
                _log.warning('Unrecognized record_type: %s; %s', record_type,
                             util.outline_gcp_project(project_index,
                                                      project, zone,
                                                      self._key_file_path))

        except Exception as e:
            _log.error('Failed to fetch details for %s; %s; error: %s: %s',
                       record_type,
                       util.outline_gcp_project(project_index, project, zone,
                                                self._key_file_path),
                       type(e).__name__, e)

        yield from self._make_record(iterator, record_type,
                                     project_index, project, zone)

    def _make_record(self, iterator, gcp_record_type, project_index, project,
                     zone):
        """Process a list of GCP resource objects.

        Arguments:
          iterator: An iterator to iterate over raw GCP ``dict`` objects.
          gcp_record_type (str): Type of record as per GCP vocabulary.
          project_index (int): Project index (for logging only).
          project (dict): GCP project object.
          zone (str): GCP zone name.

        Yields:
          dict: An GCP record that can be consumed by the framework.

        """
        record_type_map = {
            'compute': 'compute',
        }
        for i, raw_record in enumerate(iterator):
            record = {
                'raw': raw_record,
                'ext': {
                    'cloud_type': 'gcp',
                    'record_type': gcp_record_type,
                    'project_id': project.get('projectId'),
                    'project_name': project.get('name'),
                    'zone': zone,
                    'key_file_path': self._key_file_path,
                    'client_email': self._client_email
                },
                'com': {
                    'cloud_type': 'gcp',
                    'record_type': record_type_map.get(gcp_record_type)
                }
            }

            _log.info('Found %s #%d: %s; %s', gcp_record_type, i,
                      raw_record.get('name'),
                      util.outline_gcp_project(project_index, project, zone,
                                               self._key_file_path))
            yield record

            if gcp_record_type == 'firewall':
                yield from _get_normalized_firewall_rules(record,
                                                          project_index,
                                                          project,
                                                          self._key_file_path)

    def done(self):
        """Log a message that this plugin is done."""
        _log.info('Done; key_file_path: %s; processes: %s; threads: %s',
                  self._key_file_path, self._processes, self._threads)


def _get_resource_iterator(resource, key, key_file_path, **list_kwargs):
    """Generate records for specific record types.

    Arguments:
        resource (Resource): GCP resource object.
        key (str): The key that we need to look up in the GCP
            response JSON to find the list of resources.
        key_file_path (str): Path to key file (for logging only).
        list_kwargs (dict): Keyword arguments for
            ``resource.list()`` call.

    Yields:
        dict: A GCP configuration record.

    """
    try:
        request = resource.list(**list_kwargs)
        while request is not None:
            response = request.execute()
            for item in response.get(key, []):
                yield item
            request = resource.list_next(previous_request=request,
                                         previous_response=response)
    except Exception as e:
        _log.error('Failed to fetch resource list; key: %s; '
                   'list_kwargs: %s; key_file_path: %s; '
                   'error: %s: %s', key, list_kwargs,
                   key_file_path, type(e).__name__, e)


def _get_normalized_firewall_rules(firewall_record, project_index,
                                   project, key_file_path):
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
        project_index (int): Project index (for logging only).
        project (dict): GCP project object (for logging only).
        key_file_path (str): Path to key file (for logging only).

    Yield:
        dict: A normalized firewall rule record with ``com`` bucket
            populated with firewall rule properties in common notation.

    """
    allow_rules = firewall_record.get('raw', {}).get('allowed')
    if allow_rules is not None:
        for rule_index, rule in enumerate(allow_rules):
            firewall_rule = _get_normalized_firewall_rule(firewall_record,
                                                          rule_index,
                                                          rule,
                                                          project_index,
                                                          project,
                                                          key_file_path)
            firewall_rule['com']['access'] = 'allow'
            yield firewall_rule

    deny_rules = firewall_record.get('raw', {}).get('denied')
    if deny_rules is not None:
        for rule_index, rule in enumerate(deny_rules):
            firewall_rule = _get_normalized_firewall_rule(firewall_record,
                                                          rule_index,
                                                          rule,
                                                          project_index,
                                                          project,
                                                          key_file_path)
            firewall_rule['com']['access'] = 'deny'
            yield firewall_rule


def _get_normalized_firewall_rule(firewall_record, rule_index, rule,
                                  project_index, project, key_file_path):
    """Create a normalized firewall rule record.

    Arguments:
        firewall_record (dict): Firewall record generated by this plugin.
        rule_index (int): Index of a firewall rule (for logging only).
        rule (dict): Raw allowed or denied rule in ``firewall``.
        project_index (int): Project index (for logging only).
        project (dict): GCP project object (for logging only).
        key_file_path (str): Path to key file (for logging only).

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

    _log.info('Found firewall_rule #%d; %s, %s; %s', rule_index,
              raw_firewall.get('name'), rule.get('IPProtocol'),
              util.outline_gcp_project(project_index, project, None,
                                       key_file_path))
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
