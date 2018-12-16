venv: FORCE
	python3 -m venv ~/.venv/cloudmarker
	echo . ~/.venv/cloudmarker/bin/activate > venv
	. ./venv && pip3 install -r requirements.txt
	. ./venv && pip3 install -r dev-requirements.txt

rmvenv: FORCE
	rm -rf ~/.venv/cloudmarker

test: FORCE
	. ./venv && python3 -m unittest discover -v

coverage:
	. ./venv && coverage run --source . --branch -m unittest discover -v
	. ./venv && coverage report --show-missing
	. ./venv && coverage html

# See pylama.ini for pylama configuration.
lint:
	. ./venv && pylama cloudmarker

checks: test coverage lint

clean:
	find . -name "__pycache__" -exec rm -r {} +
	find . -name "*.pyc" -exec rm {} +
	rm -rf .coverage htmlcov

FORCE:
