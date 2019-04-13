"""A package for alert plugins packaged with this project.

This package contains alert plugins that are packaged as part of this
project. The alert plugins implement a function named ``write()`` that
accepts input records and typically sends them to an alerting
destination. The alert plugins also implement a function named ``done``
that perform cleanup work when called.

Note that the alert plugins implement the exact same interface as the
store plugins in the :mod:`cloudmarker.stores` package. So a store
plugin can usually serve equally well as an alert plugin, and vice
versa. In fact, some of the store plugins such as
:class:`cloudmarker.stores.esstore.EsStore` and
:class:`cloudmarker.stores.mongodbstore.MongoDBStore` are indeed used as
alert plugins too because security events can be alerted by storing them
in an Elasticsearch index or MongoDB collection.

If a plugin can serve as both a store plugin and an alert plugin, we
keep them in the :mod:`cloudmarker.stores` package. If a plugin makes
sense only as an alert plugin, we keep them in this
:mod:`cloudmarker.alerts` package.
"""
