"""Base configuration.

Attributes:
    config_yaml (str): Base configuration as YAML code.
    config_dict (dict): Base configuration as Python dictionary.

Here is the complete base configuration present as a string in the
:obj:`config_yaml` attribute::

{}

"""

import textwrap

import yaml

config_yaml = """# Base configuration
plugins:
  mockcloud:
    plugin: cloudmarker.clouds.mockcloud.MockCloud

  filestore:
    plugin: cloudmarker.stores.filestore.FileStore

  esstore:
    plugin: cloudmarker.stores.esstore.EsStore

  mongodbstore:
    plugin: cloudmarker.stores.mongodbstore.MongoDBStore

  firewallruleevent:
    plugin: cloudmarker.events.firewallruleevent.FirewallRuleEvent

  azvmosdiskencryptionevent:
    plugin: cloudmarker.events.azvmosdiskencryptionevent.AzVMOSDiskEncryptionEvent

  azvmdatadiskencryptionevent:
    plugin: cloudmarker.events.azvmdatadiskencryptionevent.AzVMDataDiskEncryptionEvent

  rdbmsenforcetlsevent:
    plugin: cloudmarker.events.rdbmsenforcetlsevent.RDBMSEnforceTLSEvent

  azwebapptlsevent:
    plugin: cloudmarker.events.azwebapptlsevent.AzWebAppTLSEvent

  azsqldatabasetdeevent:
    plugin: cloudmarker.events.azsqldatabasetdeevent.AzSQLDatabaseTDEEvent

  azlogprofileevent:
    plugin: cloudmarker.events.azlogprofileevent.AzLogProfileEvent

  azlogprofilemissingcategoryevent:
    plugin: cloudmarker.events.azlogprofilemissingcategoryevent.AzLogProfileMissingCategoryEvent

  azstorageaccountsecuretransferevent:
    plugin: cloudmarker.events.azstorageaccountsecuretransferevent.AzStorageAccountSecureTransferEvent

  azlogprofileretentionevent:
    plugin: cloudmarker.events.azlogprofileretentionevent.AzLogProfileRetentionEvent

  azkvsecretnoexpiryevent:
    plugin: cloudmarker.events.azkvsecretnoexpiryevent.AzKVSecretNoExpiryEvent

  azkvkeynoexpiryevent:
    plugin: cloudmarker.events.azkvkeynoexpiryevent.AzKVKeyNoExpiryEvent

  azkvnonrecoverableevent:
    plugin: cloudmarker.events.azkvnonrecoverableevent.AzKVNonRecoverableEvent

  azlogprofilemissinglocationevent:
    plugin: arachnoid.events.azlogprofilemissinglocationevent.AzLogProfileMissingLocationEvent

  azpostgreslogcheckpointsevent:
    plugin: cloudmarker.events.azpostgreslogcheckpointsevent.AzPostgresLogCheckpointsEvent

  azpostgreslogconnectionsevent:
    plugin: cloudmarker.events.azpostgreslogconnectionsevent.AzPostgresLogConnectionsEvent

  azpostgreslogdisconnectionsevent:
    plugin: cloudmarker.events.azpostgreslogdisconnectionsevent.AzPostgresLogDisconnectionsEvent

  azpostgreslogdurationevent:
    plugin: cloudmarker.events.azpostgreslogdurationevent.AzPostgresLogDurationEvent

  mockevent:
    plugin: cloudmarker.events.mockevent.MockEvent

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
      format: >-
          %(asctime)s [%(process)s] [%(processName)s] [%(threadName)s]
          %(levelname)s %(name)s:%(lineno)d - %(message)s
      datefmt: "%Y-%m-%d %H:%M:%S"

  handlers:
    console:
      class: logging.StreamHandler
      formatter: simple
      stream: ext://sys.stdout

    file:
      class: logging.handlers.TimedRotatingFileHandler
      formatter: simple
      filename: /tmp/cloudmarker.log
      when: midnight
      encoding: utf8
      backupCount: 5

  loggers:
    adal-python:
      level: WARNING

  root:
    level: INFO
    handlers:
      - console
      - file

schedule: "00:00"
"""


config_dict = yaml.safe_load(config_yaml)
__doc__ = __doc__.format(textwrap.indent(config_yaml, '    '))
