"""Google Cloud Platform (GCP) plugin to read GCP infrastructure data.

This module defines the :class:`GCPCloud` class that retrieves data from
Google Cloud Platform.
"""


import json

from google.oauth2 import service_account
from googleapiclient import discovery

_GCP_SCOPES = ['https://www.googleapis.com/auth/compute.readonly']
"""OAuth 2.0 scopes for Google APIs required by this plugin.

See https://developers.google.com/identity/protocols/googlescopes for
more details on OAuth 2.0 scopes for Google APIs."""


class GCPCloud:
    """GCP cloud plugin."""

    def __init__(self, service_account_key_path, zone):
        """Create an instance of :class:`GCPCloud` plugin.

        Arguments:
            service_account_key_path (str): Path of the service account
                key file for a project.
            zone (str): Zone of GCP Project, e.g., ``us-east1-b``.
        """
        self._service_account_key_path = service_account_key_path
        self._zone = zone

        # Service account key file also has the project name under the key
        # project_id. We will use this key file to get the project name for
        # this request.
        with open(self._service_account_key_path) as f:
            self._project_name = json.loads(f.read())['project_id']

        # Generating scoped credentials which will be required by the
        # discovery.build to create a resource object which we will use to
        # communicate with the API.
        credentials = service_account.Credentials
        self._credentials = credentials.from_service_account_file(
            self._service_account_key_path,
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

    def _get_firewall_rules(self):
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

        Here is an example of a firewall rule record :obj:`dict` yielded
        by this method:

        .. code:: python

            {
              "kind": "compute#firewall",
              "id": "7890789078907890",
              "creationTimestamp": "2018-12-19T01:43:51.988-08:00",
              "name": "default-allow-ss",
              "description": "str",
              "network": "https://www.googleapis.com/compute/v1/"
                         "projects/foo/global/networks/default",
              "priority": 1000,
              "sourceRanges": [
                "0.0.0.0/0"
              ],
              "targetTags": [
                "https-server"
              ],
              "allowed": [
                {
                  "IPProtocol": "tcp",
                  "ports": [
                    "80",
                    "8080-8090"
                  ]
                }
              ],
              "direction": "INGRESS",
              "logConfig": {
                "enable": bool
              },
              "disabled": bool,
              "selfLink": "https://www.googleapis.com/compute/v1/"
                          "projects/foo/global/firewalls/default-allow-https",
              "record_type": "firewall_rule"
            }

        """
        firewall_rules = self._get_firewall_rules()
        instances = self._get_instances()

        for rule in firewall_rules:
            rule.update({'record_type': 'firewall_rule'})
            yield rule

        for instance in instances:
            instance.update({'record_type': 'compute_instance'})
            yield instance

    def done(self):
        """Perform clean up tasks.

        Currently, this method does nothing because there are no clean
        up tasks associated with the :class:`GCPCloud` plugin. This
        may change in future.
        """
