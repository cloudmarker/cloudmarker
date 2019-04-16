"""Base configuration.

Attributes:
    config_yaml (str): Base configuration as YAML code.
    config_dict (dict): Base configuration as Python dictionary.

Examples:
    Here are a few examples that show how the values of these attributes
    look::

        >>> from cloudmarker import baseconfig
        >>> print(baseconfig.config_yaml) # doctest: +ELLIPSIS
        # Base configuration
        clouds:
          mockcloud:
            plugin: cloudmarker.clouds.mockcloud.MockCloud
        ...
        >>> baseconfig.config_dict['clouds']
        {'mockcloud': {'plugin': 'cloudmarker.clouds.mockcloud.MockCloud'}}
        >>> baseconfig.config_dict['audits'] # doctest: +ELLIPSIS
        {'mockaudit': {...}}
        >>> baseconfig.config_dict['audits']['mockaudit']['clouds']
        ['mockcloud']

    .. Note that it is necessary to put the above example in a
       reStructuredText literal code block created with the "::" marker
       so that the doctest directive "# doctest: +ELLIPSIS" does not
       appear in the rendered documentation.

"""

import yaml

config_yaml = """# Base configuration
clouds:
  mockcloud:
    plugin: cloudmarker.clouds.mockcloud.MockCloud

stores:
  esstore:
    plugin: cloudmarker.stores.esstore.EsStore
  filestore:
    plugin: cloudmarker.stores.filestore.FileStore
  mongodbstore:
    plugin: cloudmarker.stores.mongodbstore.MongoDBStore

events:
  firewallruleevent:
    plugin: cloudmarker.events.firewallevent.FirewallRuleEvent
  mockevent:
    plugin: cloudmarker.events.mockevent.MockEvent

alerts:
  filestore:
    plugin: cloudmarker.stores.filestore.FileStore

audits:
  mockaudit:
    clouds:
      - mockcloud
    stores:
      - filestore
    events:
      - mockevent
    alerts:
      - filestore

run:
  - mockaudit

logger:
  version: 1

  disable_existing_loggers: false

  formatters:
    simple:
      format: "%(asctime)s %(levelname)s %(name)s:%(lineno)d - %(message)s"
      datefmt: "%Y-%m-%d %H:%M:%S"

  handlers:
    console:
      class: logging.StreamHandler
      level: DEBUG
      formatter: simple
      stream: ext://sys.stdout

    file_handler:
      class: logging.handlers.TimedRotatingFileHandler
      level: DEBUG
      formatter: simple
      filename: logs/cloudmarker.log
      when: midnight
      encoding: utf8

  loggers:
    adal-python:
      level: WARNING

  root:
    level: INFO
    handlers:
      - console
      - file_handler

schedule: "00:00"
"""


config_dict = yaml.safe_load(config_yaml)
