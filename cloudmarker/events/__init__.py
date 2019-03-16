"""A package for event plugins packaged with this project.

This package contains event plugins that are packaged as part of this
project. The event plugins implement a function named ``eval`` that
accepts one record as parameter, evaluates the record, and generates
zero or more event records for each input record. The event plugins also
implement and a function named ``done`` that perform cleanup work when
called.
"""
