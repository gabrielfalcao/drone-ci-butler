.PHONY: all develop tests dependencies unit functional tdd-functional tdd-unit run clean black db-migrate db-create

PACKAGE_NAME		:= drone_ci_butler
MAIN_CLI_NAME		:= drone-ci-butler
REQUIREMENTS_FILE	:= development.txt
GIT_ROOT		:= $(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))
PACKAGE_PATH		:= $(GIT_ROOT)/$(PACKAGE_NAME)
VENV_ROOT		:= $(GIT_ROOT)/.venv
MAIN_CLI_PATH		:= $(VENV_ROOT)/$(MAIN_CLI_NAME)
PIP_INSTALL		:= $(VENV_ROOT)/bin/pip install --use-deprecated=legacy-resolver
export ALEMBIC_CONFIG	?= $(PACKAGE_PATH)/alembic.ini
export VENV		?= $(VENV_ROOT)

all: dependencies tests

venv $(VENV):  # creates $(VENV) folder if does not exist
	python3 -mvenv $(VENV)
	$(PIP_INSTALL) -U pip setuptools

$(VENV)/bin/alembic $(MAIN_CLI_PATH) $(VENV)/bin/nosetests $(VENV)/bin/python $(VENV)/bin/pip develop: # installs latest pip
	test -e $(VENV)/bin/pip || $(MAKE) $(VENV)
	$(PIP_INSTALL) --force-reinstall -r $(REQUIREMENTS_FILE)
	$(VENV)/bin/python setup.py develop

# Runs the unit and functional tests
tests: unit functional  # runs all tests

db-create:
	-@dropdb drone_ci_butler
	-@dropuser drone_ci_butler
	-@createuser drone_ci_butler
	-@createdb --owner=drone_ci_butler drone_ci_butler

db-migrate: db-create
	(cd $(PACKAGE_PATH) && $(VENV)/bin/alembic upgrade head)

# Install dependencies
dependencies: | $(VENV)/bin/nosetests
	$(PIP_INSTALL) -r $(REQUIREMENTS_FILE)
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
