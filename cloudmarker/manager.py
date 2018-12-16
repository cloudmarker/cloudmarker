#!/usr/bin/env python


"""Manager of worker processes.

This module invokes the worker processes that perform the cloud security
monitoring tasks.
"""


from cloudmarker import util


def main():
    """Run the framework."""
    args = util.parse_cli()
    config = util.load_config(args.config)
    print(config)
