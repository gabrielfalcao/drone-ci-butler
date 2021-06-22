MAKEFILE_PATH		:= $(realpath $(firstword $(MAKEFILE_LIST)))
GIT_ROOT		:= $(shell dirname $(MAKEFILE_PATH))
VENV_ROOT		:= $(GIT_ROOT)/.venv

PACKAGE_NAME		:= drone_ci_butler
MAIN_CLI_NAME		:= drone-ci-butler
REQUIREMENTS_FILE	:= development.txt

NODE_MODULES		:= $(GIT_ROOT)/frontend/node_modules
PACKAGE_PATH		:= $(GIT_ROOT)/$(PACKAGE_NAME)
REQUIREMENTS_PATH	:= $(GIT_ROOT)/$(REQUIREMENTS_FILE)
MAIN_CLI_PATH		:= $(VENV_ROOT)/bin/$(MAIN_CLI_NAME)
export VENV		?= $(VENV_ROOT)
WEB_PORT		:= 4000
WEB_HOST		:= 0.0.0.0
STATIC_PATHS		:= $(patsubst %,frontend/public/%, manifest.json asset-manifest.json favicon.ico index.html robots.txt static)
DOCKER_ENV		:= $(GIT_ROOT)/tools/docker.env
BUILD_PATHS		:= build docs/build frontend/build
######################################################################
# webpack env vars
export BUILD_PATH	:= $(GIT_ROOT)/drone_ci_butler/web/public
export PUBLIC_URL	:= https://drone-ci-butler.ngrok.io/
export NODE_ENV		:= production
######################################################################
# tool env vars
export DRONE_CI_BUTLER_CONFIG_PATH := ~/.drone-ci-butler.yml

######################################################################
# Phony targets (only exist for typing convenience and don't represent
#                real paths as Makefile expects)
######################################################################

# default target when running `make` without arguments
all: | $(MAIN_CLI_PATH)

env-docker: | $(DOCKER_ENV)

compose:
	docker-compose up --abort-on-container-exit --force-recreate --build

db-create:
	@./tools/recreate-db drone_ci_butler

drone-db-create:
	@./tools/recreate-db drone-ci-server drone-ci-server

db-migrate: | $(VENV)/bin/alembic
	@echo "running migrations"
	$(MAIN_CLI_PATH) migrate-db --target head

tunnel:
	ngrok http --subdomain drone-ci-butler $(WEB_PORT)

ci-tunnel:
	ngrok http --subdomain drone-ci-server 8000

db: db-create db-migrate
# creates virtualenv
venv: | $(VENV)

# updates pip and setuptools to their latest version
develop: | $(VENV)/bin/python $(VENV)/bin/pip

# installs the requirements and the package dependencies
setup: | $(MAIN_CLI_PATH)
public: | $(STATIC_PATHS)

# Convenience target to ensure that the venv exists and all
# requirements are installed
dependencies:
	@rm -f $(MAIN_CLI_PATH) # remove MAIN_CLI_PATH to trigger pip install
	$(MAKE) develop setup

# Run all tests, separately
tests: unit functional | $(MAIN_CLI_PATH)  # runs all tests

# -> unit tests
unit functional: | $(VENV)/bin/pytest # runs only unit tests
	@DRONE_CI_BUTLER_CONFIG_PATH=$(GIT_ROOT)/tests/drone-ci-butler.yml \
		$(VENV)/bin/pytest tests/$@

# functional: | $(VENV)/bin/nosetests
#	DRONE_CI_BUTLER_CONFIG_PATH=$(GIT_ROOT)/tests/drone-ci-butler.yml \
#	 	@$(VENV)/bin/nosetests tests/$@

# -> unit tests
tdd: | $(VENV)/bin/nosetests  # runs only unit tests
	@$(VENV)/bin/ptw  -- --capture=no -vv --cov=drone_ci_butler.rule_engine tests/unit



# run main command-line tool
workers builds: | $(MAIN_CLI_PATH)
	@$(MAIN_CLI_PATH) $@

purge: | $(MAIN_CLI_PATH)
	@$(MAIN_CLI_PATH) purge --http-cache --elasticsearch

# run webapp
web: | $(MAIN_CLI_PATH)
	@DRONE_CI_BUTLER_CONFIG_PATH=~/.drone-ci-butler.yml $(MAIN_CLI_PATH) web -H $(WEB_HOST) -P $(WEB_PORT) --migrate

# Pushes release of this package to pypi
release-push:  # pushes distribution tarballs of the current version
	$(VENV)/bin/twine upload dist/*.tar.gz

# Prepares release of this package prior to pushing to pypi
release-build:
	rm -rf ./dist  # remove local packages
	$(VENV)/bin/twine check dist/*.tar.gz
	$(VENV)/bin/python setup.py build sdist

# Convenience target that runs all tests then builds and pushes a release to pypi
release: tests release-build release-push
	$(MAKE) release-build
	$(MAKE) release-push

# Convenience target to delete the virtualenv
clean:
	@rm -f $(DOCKER_ENV)
	@rm -rf $(BUILD_PATHS)

# Convenience target to format code with black with PEP8's default
# 80 character limit per line
black: | $(VENV)/bin/black
	@$(VENV)/bin/black -l 80 $(PACKAGE_PATH) tests

##############################################################
# Real targets (only run target if its file has been "made" by
#               Makefile yet)
##############################################################

$(NODE_MODULES):
	cd frontend && yarn

react-app $(STATIC_PATHS): | $(NODE_MODULES)
	@cd frontend && yarn build
	@rsync -putao $(GIT_ROOT)/frontend/build/ $(GIT_ROOT)/drone_ci_butler/web/public/

react-dev: | $(STATIC_PATHS)
	@cd frontend && yarn start

docker-base:
	docker build -t gabrielfalcao/drone-ci-butler-base -f Dockerfile.base .

docker-k8s:
	docker build -t gabrielfalcao/drone-ci-butler:1 -f Dockerfile .

# creates virtual env if necessary and installs pip and setuptools
$(VENV): | $(REQUIREMENTS_PATH)  # creates $(VENV) folder if does not exist
	echo "Creating virtualenv in $(VENV_ROOT)" && python3 -mvenv $(VENV)

# installs pip and setuptools in their latest version, creates virtualenv if necessary
$(VENV)/bin/python $(VENV)/bin/pip: # installs latest pip
	@test -e $(VENV)/bin/python || $(MAKE) $(VENV)
	@test -e $(VENV)/bin/pip || $(MAKE) $(VENV)

 # installs latest version of the "black" code formatting tool
$(VENV)/bin/black: | $(VENV)/bin/pip
	$(VENV)/bin/pip install -U black

# installs this package in "edit" mode after ensuring its requirements are installed
$(VENV)/bin/alembic $(VENV)/bin/pytest $(VENV)/bin/nosetests $(MAIN_CLI_PATH): | $(VENV) $(VENV)/bin/pip $(VENV)/bin/python $(REQUIREMENTS_PATH)
	$(VENV)/bin/pip install -r $(REQUIREMENTS_PATH)
	$(VENV)/bin/pip install -e .

# ensure that REQUIREMENTS_PATH exists
$(REQUIREMENTS_PATH):
	@echo "The requirements file $(REQUIREMENTS_PATH) does not exist"
	@echo ""
	@echo "To fix this issue:"
	@echo "  edit the variable REQUIREMENTS_NAME inside of the file:"
	@echo "  $(MAKEFILE_PATH)."
	@echo ""
	@exit 1

$(DOCKER_ENV): clean
	@$(MAIN_CLI_PATH) env > $@
	@echo CREATED $@
###############################################################
# Declare all target names that exist for convenience and don't
# represent real paths, which is what Make expects by default:
###############################################################

.PHONY: \
	all \
	black \
	release-build \
	clean \
	compose \
	dependencies \
	develop \
	release-push \
	release \
	setup \
	run \
	tests \
	unit \
	functional \
	workers \
	builds \
	public \
	react-app \
	tunnel \
	tdd \
	purge \
	web \
	env-docker \
	docker-base \
	docker-k8s
