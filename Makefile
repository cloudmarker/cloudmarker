venv: FORCE
	python3 -m venv ~/.venv/cloudmarker
	echo . ~/.venv/cloudmarker/bin/activate > venv

# In local development environment, we run `make venv` to create a
# `venv` script that can be used to activate the virtual Python
# environment conveniently by running `. ./venv`.
#
# However, Travis CI creates virtual Python environments on its own for
# each Python version found in the build matrix. Further, in certain
# production environments, we may not want to create virtual Python
# environments.
#
# In both of the above mentioned cases, we do not run `make venv`. But
# most of the commands below start with `. ./venv`, so a `venv` script
# is expected by all the commands. Therefore, we run `touch venv` to
# create an empty `venv` script if none exists. If `venv` already
# exists, then `touch venv` does nothing apart from altering its access
# and modification times.
deps: FORCE
	touch venv
	. ./venv && pip3 install -r requirements.txt
	. ./venv && pip3 install -r dev-requirements.txt
	mkdir logs

rmvenv: FORCE
	rm -rf ~/.venv/cloudmarker

test: FORCE
	# Test interactive Python examples in docstrings.
	. ./venv && find . -name "*.py" ! -name "__main__.py" | \
	            xargs -n 1 python3 -m doctest
	# Run unit tests.
	. ./venv && python3 -m unittest -v

coverage: FORCE
	. ./venv && coverage run -m unittest -v
	. ./venv && coverage combine
	. ./venv && coverage report --show-missing
	. ./venv && coverage html
	@echo
	@echo Coverage report: htmlcov/index.html

# See pylama.ini for pylama configuration. Pylama is configured to
# invoke isort to lint import statements. Pylama prints the files where
# we need to fix the import statements. But it does not tell us the
# details of the changes to be made to fix them.
#
# This is why we invoke isort independently once to show us the changes
# (in diff format) that we need to make to fix the import statements.
# Note that this independently invoked isort exits with exit code 0
# regardless of whether it finds problems with import statements or not.
lint: FORCE
	. ./venv && isort --quiet --diff
	. ./venv && pylama

# The -M option for sphinx-apidoc puts the package documentation before
# submodules documentation. Without it, the package documentation is
# placed after submodules documentation.
docs: FORCE
	rm -rf docs/api docs/_build
	. ./venv && sphinx-apidoc -M -o docs/api cloudmarker cloudmarker/test
	. ./venv && cd docs && make html
	@echo
	@echo Generated documentation: docs/_build/html/index.html

checks: test coverage lint docs

clean: FORCE
	find . -name "__pycache__" -exec rm -r {} +
	find . -name "*.pyc" -exec rm {} +
	rm -rf .coverage.* .coverage htmlcov

FORCE:
