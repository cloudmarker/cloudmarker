"""Utility functions."""


import argparse
import copy
import os

import yaml


def load_config(config_paths):
    """Load configuration from specified configuration paths.

    Arguments:
        config_paths (list): Configuration paths.

    Returns:
        dict: A dictionary of configuration key-value pairs.

    """
    config = {}

    for config_path in config_paths:
        if not os.path.exists(config_path):
            # TODO: Log warning after logging is included.
            continue

        with open(config_path) as f:
            new_config = yaml.load(f)
            config = merge_dicts(config, new_config)

    return config


def parse_cli(args=None):
    """Parse command line arguments.

    Arguments:
        args (list): List of command line arguments.

    Returns:
        argparse.Namespace: Parsed command line arguments.

    """
    parser = argparse.ArgumentParser(prog='cloudmarker')
    parser.add_argument('-c', '--config', nargs='+',
                        default=['config.base.yaml', 'config.yaml'],
                        help='Configuration file paths')
    args = parser.parse_args(args)
    return args


def merge_dicts(a, b):
    """Recursively merge two dictionaries."""
    c = copy.deepcopy(a)
    for k in b:
        if (k in a and isinstance(a[k], dict) and isinstance(b[k], dict)):
            c[k] = merge_dicts(a[k], b[k])
        else:
            c[k] = copy.deepcopy(b[k])
    return c
