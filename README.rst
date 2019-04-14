Cloudmarker
===========

Cloudmarker is a cloud monitoring tool and framework.

.. image:: https://travis-ci.com/cloudmarker/cloudmarker.svg?branch=master
    :target: https://travis-ci.com/cloudmarker/cloudmarker

.. image:: https://coveralls.io/repos/github/cloudmarker/cloudmarker/badge.svg?branch=master
    :target: https://coveralls.io/github/cloudmarker/cloudmarker?branch=master

.. image:: https://img.shields.io/badge/license-MIT-blue.svg
   :target: https://github.com/cloudmarker/cloudmarker/blob/master/LICENSE.rst


Contents
--------

.. contents:: Table of Contents:
    :backlinks: none


What is Cloudmarker?
--------------------

Cloudmarker is a cloud monitoring tool and framework. It can be used as
a ready-made tool that audits your Azure or GCP cloud environments as
well as a framework that allows you to develop your own cloud monitoring
software to audit your clouds.

As a monitoring tool, it performs the following actions:

- Retrieves data about each configured cloud using the cloud APIs.
- Saves or indexes the retrieved data into each configured storage
  system or indexing engine.
- Analyzes the data for potential issues and generates events that
  represent the detected issues.
- Saves the events to configured storage or indexing engines as well as
  sends the events as alerts to alerting destinations.

Each of the above four aspects of the tool can be configured via a
configuration file.

For example, the tool can be configured to pull data from Azure and
index its data in Elasticsearch while it also pulls data from GCP and
indexes the GCP data in MongoDB. Similarly, it is possible to configure
the tool to check for unencrypted disks in Azure, generate events for
it, and send them as alerts by email while it checks for insecure
firewall rules in both Azure and GCP, generate events for them, and save
those events in MongoDB.

This degree of flexibility to configure audits for different clouds in
different ways comes from the fact that Cloudmarker is designed as a
combination of lightweight framework and a bunch of plugins that do the
heavylifting for retrieving cloud data, storing the data, analyzing
the data, generating events, and sending alerts. These four types of
plugins are formally known as cloud plugins, store plugins, event
plugins, and alert plugins, respectively.

As a result of this plugin-based architecture, Cloudmarker can also be
used as a framework to develop your own plugins that extend its
capabilities by adding support for new types of clouds or data sources,
storage or indexing engines, event generation, and alerting
destinations.


Why Cloudmarker?
----------------

One might wonder why we need a new project like this when similar
projects exist. When we began working on this project in 2017, we were
aware of similar tools that supported AWS and GCP but none that
supported Azure at that time. As a result, we wrote our own tool to
support Azure. We later added support for GCP as well. What began as a
tiny proof of concept gradually turned into a fair amount of code, so we
thought, we might as well share this project online, so that others
could use it and see if they find value in it.

So far, some of the highlights of this project are:

- It is simple. It is easy to understand how to use the four types of
  plugins (clouds, stores, events, and alerts) to perform an audit.
- It is excellent at creating an inventory of the cloud environment.
- The data inventory it creates is easy to query.
- It is good at detecting insecure firewall rules and unencrypted disks.
  New detection mechanisms are coming up.

We also realize that we can add a lot more functionality to this project
to make it more powerful too. See the `Wishlist`_ section below to see
new features we would like to see in this project. Our project is hosted
on GitHub at https://github.com/cloudmarker/cloudmarker. Contributions
and pull requests are welcome.

We hope that you would give this project a shot, see if it addresses
your needs, and provide us some feedback by posting a comment in our
`feedback thread <https://github.com/cloudmarker/cloudmarker/issues/100>`_
or by creating a
`new issue <https://github.com/cloudmarker/cloudmarker/issues/new>`_.


Features
--------

Since Cloudmarker is not just a tool but also a framework, a lot of its
functionality can be extended by writing plugins. However, Cloudmarker
also comes bundled with a default set of plugins that can be used as is
without writing a single line of code. Here is a brief overview of the
features that come bundled with Cloudmarker:

- Perform scheduled or ad hoc audits of cloud environment.
- Retrieve data from Azure and GCP.
- Store or index retrieved data in Elasticsearch, MongoDB, Splunk, and
  the file system.
- Look for insecure firewall rules and generate firewall rule events.
- Look for unencrypted disks (Azure only) and generate events.
- Send alerts for events via email and Slack as well as save alerts in
  one of the supported storage or indexing engines (see the third point
  above).
- Normalize firewall rules from Azure and GCP which are in different
  formats to a common object model (``"com"``) so that a single query or
  event rule can search for or detect issues in firewall rules from both
  clouds.


Wishlist
--------

- Add more event plugins to detect different types of insecure
  configuration.
- Normalize other types of data into a common object model (``"com"``)
  just like we do right now for firewall rules.


Install
-------

Perform the following steps to set up Cloudmarker.

1. Create a virtual Python environment and install Cloudmarker in it:

   .. code-block:: sh

    python3 -m venv venv
    . venv/bin/activate
    pip3 install cloudmarker

2. Run sanity test:

   .. code-block:: sh

    cloudmarker -n

   The above command runs a mock audit with mock plugins that generate
   some mock data. The mock data generated can be found at
   ``/tmp/cloudmarker/``. Logs from the tool are written to the standard
   output as well as to ``/tmp/cloudmarker.log``.

   The ``-n`` or ``--now`` option tells Cloudmarker to run right now
   instead of waiting for a scheduled run.

To learn how to configure and use Cloudmarker with Azure or GCP clouds,
see `Cloudmarker Tutorial`_.


Develop
-------

This section describes how to set up a development environment for
Cloudmarker. This section is useful for those who would like to
contribute to Cloudmarker or run Cloudmarker directly from its source.

1. We use primarily three tools to perform development on this project:
   Python 3, Git, and Make. Your system may already have these tools.
   But if not, here are some brief instructions on how they can be
   installed.

   On macOS, if you have `Homebrew <https://brew.sh/>`_ installed, then
   these tools can be be installed easily with the following command:

   .. code-block:: sh

    brew install python git

   On a Debian GNU/Linux system or in another Debian-based Linux
   distribution, they can be installed with the following commands:

   .. code-block:: sh

    apt-get update
    apt-get install python3 python3-venv git make

   On a CentOS Linux distribution, they can be installed with these
   commands:

   .. code-block:: sh

    yum install centos-release-scl
    yum install git make rh-python36
    scl enable rh-python36 bash

   Note: The ``scl enable`` command starts a new shell for you to use
   Python 3.

   On any other system, we hope you can figure out how to install these
   tools yourself.

2. Clone the project repository and enter its top-level directory:

   .. code-block:: sh

    git clone https://github.com/cloudmarker/cloudmarker.git
    cd cloudmarker

3. Create a virtual Python environment for development purpose:

   .. code-block:: sh

    make venv deps

   This creates a virtual Python environment at ``~/.venv/cloudmarker``.
   Additionally, it also creates a convenience script named ``venv`` in
   the current directory to easily activate the virtual Python
   environment which we will soon see in the next point.

   To undo this step at anytime in future, i.e., delete the virtual
   Python environment directory, either enter
   ``rm -rf venv ~/.venv/cloudmarker`` or enter ``make rmvenv``.

4. Activate the virtual Python environment:

   .. code-block:: sh

    . ./venv

5. In the top-level directory of the project, enter this command:

   .. code-block:: sh

    python3 -m cloudmarker -n

   This generates mock data at ``/tmp/cloudmarker``. This step serves as
   a sanity check that ensures that the development environment is
   correctly set up and that the Cloudmarker audit framework is running
   properly.

6. Now that the project is set up correctly, you can create a
   ``cloudmarker.yaml`` to configure Cloudmarker to scan/audit your
   cloud or you can perform more development on the Cloudmarker source
   code. See `Cloudmarker Tutorial`_ for more details.

7. If you have set up a development environment to perform more
   development on Cloudmarker, please consider sending a pull request to
   us if you think your development work would be useful to the
   community.

8. Before sending a pull request, please run the unit tests, code
   coverage, linters, and document generator to ensure that no existing
   test has been broken and the pull request adheres to our coding
   conventions:

   .. code-block:: sh

    make test
    make coverage
    make lint
    make docs

   To run these four targets in one shot, enter this "shortcut" target:

   .. code-block:: sh

    make checks

   Open ``htmlcov/index.html`` with a web browser to view the code
   coverage report.

   Open ``docs/_build/html/index.html`` with a web browser to view the
   generated documentation.


Resources
---------

Here is a list of useful links about this project:

- `Documentation on Read The Docs <https://cloudmarker.readthedocs.org/>`_
- `Latest release on PyPI <https://pypi.python.org/pypi/cloudmarker>`_
- `Source code on GitHub <https://github.com/cloudmarker/cloudmarker>`_
- `Issue tracker on GitHub <https://github.com/cloudmarker/cloudmarker/issues>`_
- `Changelog on GitHub <https://github.com/cloudmarker/cloudmarker/blob/master/CHANGES.rst>`_
- `Cloudmarker channel on Slack <https://cloudmarker.slack.com/>`_
- `Invitation to Cloudmarker channel on Slack <https://bit.ly/cmslack>`_


Support
-------

To report bugs, suggest improvements, or ask questions, please create a
new issue at http://github.com/cloudmarker/cloudmarker/issues.


License
-------

This is free software. You are permitted to use, copy, modify, merge,
publish, distribute, sublicense, and/or sell copies of it, under the
terms of the MIT License. See `LICENSE.rst`_ for the complete license.

This software is provided WITHOUT ANY WARRANTY; without even the implied
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
`LICENSE.rst`_ for the complete disclaimer.

.. _LICENSE.rst: https://github.com/cloudmarker/cloudmarker/blob/master/LICENSE.rst
.. _Cloudmarker Tutorial: https://cloudmarker.readthedocs.io/en/latest/tutorial.html
.. _Cloudmarker API: https://cloudmarker.readthedocs.io/en/latest/api/modules.html

