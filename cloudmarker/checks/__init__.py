"""A package for check plugins packaged with this project.

This package contains check plugins that are packaged as part of this
project. The check plugins implement a function named ``eval`` that
accepts one record as parameter, evaluates the record, and generates
zero or more event records for each input record. The check plugins also
implement and a function named ``done`` that perform cleanup work when
called.
"""
