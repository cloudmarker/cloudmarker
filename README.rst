Cloudmarker
============

Cloudmarker is a cloud security monitoring framework.


Setup Development Environment
-----------------------------

Please follow these steps to setup the development environment:

1. Ensure Python 3 is installed. ::

    # On macOS
    brew install python

2. Clone the project repository. ::

    git clone https://github.com/cloudmarker/cloudmarker.git

3. Create a virtual Python environment for development purpose: ::

    make venv deps

4. Activate the virtual Python environment: ::

    . ./venv

5. In the top-level directory of the project, enter this command: ::

    python3 -m cloudmarker

   Right now, it generates mock data at ``/tmp/cloudmarker``. More
   functionality will be added later.

6. Run the unit tests, code coverage, linters, and document generator: ::

    make test
    make coverage
    make lint
    make docs

   To run these four targets in one shot, enter this "shortcut" target: ::

    make checks

   Open ``htmlcov/index.html`` with a web browser to view the code
   coverage report.

   Open ``docs/_build/html/index.html`` with a web browser to view the
   generated documentation.
