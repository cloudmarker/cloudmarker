Cloud Marker
============

Cloud Marker is a cloud security monitoring framework.


Setup Development Environment
-----------------------------

Please follow these steps to setup the development environment:

 1. Ensure Python 3 is installed.

        # On macOS
        brew install python

 2. Clone the project repository.

        git clone https://github.com/cloudmarker/cloudmarker.git

 3. Create a virtual Python environment for development purpose:

        make venv deps

 4. Activate the virtual Python environment:

        . ./venv

 5. In the top-level directory of the project, enter this command:

        python3 -m cloudmarker

    Right now, it just reads a default configuration and prints it. More
    functionality will be added later.

 6. Run the unit tests, code coverage, and linters:

        make test
        make coverage
        make lint

    To run all of them in one shot, enter this "shortcut" target:

        make checks
