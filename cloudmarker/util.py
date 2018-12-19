"""Utility functions."""


import argparse
import copy
import importlib
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


def load_plugin(plugin_config):
    """Construct an object with specified plugin class and parameters.

    The plugin_config parameter must be a dictionary with the following
    keys:

      - 'plugin': The value for this key must be a string that
        represents the fully qualified class name of the plugin. The
        fully qualified class name is in the dotted notation, e.g.,
        ``pkg.module.ClassName``.
      - 'params': The value for this key must be a dict that represents
        the parameters to be passed to the ``__init__`` function of the
        plugin class. Each key in the dictionary represents the
        parameter name and each value represents the value of the
        parameter.

    Arguments:
        plugin_config (dict): Plugin configuration dictionary.

    Returns:
        object: An object of type mentioned in the ``plugin`` parameter.

    """
    # Split the fully qualified class name into module and class names.
    parts = plugin_config['plugin'].rsplit('.', 1)

    # Validate that the fully qualified class name had at least two
    # parts: module name and class name.
    if len(parts) < 2:
        msg = ('Invalid plugin class name: {}; expected format: '
               '[<pkg>.]<module>.<class>'.format(plugin_config['plugin']))
        raise PluginError(msg)

    # Load the specified adapter class from the specified module.
    plugin_module = importlib.import_module(parts[0])
    plugin_class = getattr(plugin_module, parts[1])

    # Initialize params to empty dictionary if none was specified.
    plugin_params = plugin_config.get('params', {})

    # Construct the plugin.
    plugin = plugin_class(**plugin_params)
    return plugin


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


class PluginError(Exception):
    """Plugin related error."""
