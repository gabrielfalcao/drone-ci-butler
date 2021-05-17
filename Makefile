.PHONY: all develop tests dependencies unit functional tdd-functional tdd-unit run clean black

PACKAGE_PATH		:= ./drone_ci_butler
MAIN_CLI_NAME		:= drone-ci-butler
REQUIREMENTS_FILE	:= development.txt
GIT_ROOT		:= $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
VENV_ROOT		:= $(GIT_ROOT)/.venv
MAIN_CLI_PATH		:= $(VENV_ROOT)/$(MAIN_CLI_NAME)
export VENV		?= $(VENV_ROOT)
all: dependencies tests

venv $(VENV):  # creates $(VENV) folder if does not exist
	python3 -mvenv $(VENV)
	$(VENV)/bin/pip install -U pip setuptools

develop $(MAIN_CLI_PATH) $(VENV)/bin/nosetests $(VENV)/bin/python $(VENV)/bin/pip: # installs latest pip
	test -e $(VENV)/bin/pip || $(MAKE) $(VENV)
	$(VENV)/bin/pip install --force-reinstall -r $(REQUIREMENTS_FILE)
	$(VENV)/bin/python setup.py develop

# Runs the unit and functional tests
tests: unit functional  # runs all tests


# Install dependencies
dependencies: | $(VENV)/bin/nosetests
	$(VENV)/bin/pip install -r $(REQUIREMENTS_FILE)
	$(VENV)/bin/python setup.py develop


# runs unit tests
unit: | $(VENV)/bin/nosetests  # runs only unit tests
	$(VENV)/bin/nosetests --cover-erase tests/unit


# runs functional tests
functional:| $(VENV)/bin/nosetests  # runs functional tests
	$(VENV)/bin/nosetests tests/functional

run: | $(VENV)/bin/python
	@$(MAIN_CLI_PATH) --help

push-release:  # pushes distribution tarballs of the current version
	$(VENV)/bin/twine check dist/*.tar.gz
	$(VENV)/bin/twine upload dist/*.tar.gz

build-release:
	rm -rf ./dist  # remove local packages
	$(VENV)/bin/twine check dist/*.tar.gz
	$(VENV)/bin/twine upload dist/*.tar.gz

release: tests build-release push-release
	$(MAKE) build-release
	$(MAKE) push-release

clean:
	rm -rf .venv

black:
	black -l 79 $(PACKAGE_PATH) tests
