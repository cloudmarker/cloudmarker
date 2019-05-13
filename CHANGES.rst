Changelog
=========

0.1.0 (2019-05-13)
------------------

Added
^^^^^

- Add audit version string to all generated records.
- Add "About" field in the email body of audit notification emails.
- Add ``AzVMOSDiskEncryptionEvent`` plugin to detect unencrypted OS disks.
- Add ``AzVMDataDiskEncryptionEvent`` plugin to detect unencrypted data disks.


0.0.5 (2019-04-25)
------------------

Added
^^^^^

- Add ``FirewallRuleEvent`` plugin to detect insecure firewall rules.
- Add ``EsStore`` plugin to index data in Elasticsearch.
- Add ``EmailAlert`` plugin to send alerts.
- Add ``SlackAlert`` plugin to send alerts.
- Add ``AzVM`` plugin to pull Azure virtual machine details and instance views.

Changed
^^^^^^^

- Rename ``AzureCloud`` to ``AzCloud``.

0.0.4 (2019-02-25)
------------------

Added
^^^^^

- Add ``AzureCloud`` plugin to pull Azure cloud resources.


0.0.3 (2019-02-02)
------------------

Added
^^^^^

- Add ``MongoDBStore`` plugin to store data in MongoDB.


0.0.2 (2019-01-07)
------------------

Added
^^^^^

- Add ``GCPCloud`` plugin to pull compute and firewall rules.


0.0.1 (2018-12-25)
------------------

Added
^^^^^

- Multiprocessing-based cloud monitoring framework.
