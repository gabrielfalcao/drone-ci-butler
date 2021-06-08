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

######################################################################
# webpack env vars
export BUILD_PATH	:= $(GIT_ROOT)/drone_ci_butler/web/public
export PUBLIC_URL	:= https://drone-ci-butler.ngrok.io/
export NODE_ENV		:= production

######################################################################
# Phony targets (only exist for typing convenience and don't represent
#                real paths as Makefile expects)
######################################################################

# default target when running `make` without arguments
all: | $(MAIN_CLI_PATH)

db-create:
	@./tools/recreate-db drone_ci_butler

drone-db-create:
	@./tools/recreate-db drone-ci-server drone-ci-server

db-migrate: | $(VENV)/bin/alembic
	@echo "running migrations"
	@(cd $(PACKAGE_PATH) && $(VENV)/bin/alembic upgrade head)

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
unit: | $(VENV)/bin/nosetests  # runs only unit tests
	@$(VENV)/bin/nosetests --cover-erase tests/unit

# -> functional tests
functional:| $(VENV)/bin/nosetests  # runs functional tests
	@$(VENV)/bin/nosetests tests/functional

# run main command-line tool
builds workers: | $(MAIN_CLI_PATH)
	@$(MAIN_CLI_PATH) $@

# run webapp
web: | $(MAIN_CLI_PATH)
	@$(MAIN_CLI_PATH) web -H $(WEB_HOST) -P $(WEB_PORT) --debug

# Pushes release of this package to pypi
push-release:  # pushes distribution tarballs of the current version
	$(VENV)/bin/twine upload dist/*.tar.gz

# Prepares release of this package prior to pushing to pypi
build-release:
	rm -rf ./dist  # remove local packages
	$(VENV)/bin/twine check dist/*.tar.gz
	$(VENV)/bin/python setup.py build sdist

# Convenience target that runs all tests then builds and pushes a release to pypi
release: tests build-release push-release
	$(MAKE) build-release
	$(MAKE) push-release

# Convenience target to delete the virtualenv
clean:
	@rm -rf .venv

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

# creates virtual env if necessary and installs pip and setuptools
$(VENV): | $(REQUIREMENTS_PATH)  # creates $(VENV) folder if does not exist
	echo "Creating virtualenv in $(VENV_ROOT)" && python3 -mvenv $(VENV)

# installs pip and setuptools in their latest version, creates virtualenv if necessary
$(VENV)/bin/python $(VENV)/bin/pip: # installs latest pip
	@test -e $(VENV)/bin/python || $(MAKE) $(VENV)
	@test -e $(VENV)/bin/pip || $(MAKE) $(VENV)
	@echo "Installing latest version of pip and setuptools"
	@$(VENV)/bin/pip install -U pip setuptools

 # installs latest version of the "black" code formatting tool
$(VENV)/bin/black: | $(VENV)/bin/pip
	$(VENV)/bin/pip install -U black

# installs this package in "edit" mode after ensuring its requirements are installed
$(VENV)/bin/alembic $(VENV)/bin/nosetests $(MAIN_CLI_PATH): | $(VENV) $(VENV)/bin/pip $(VENV)/bin/python $(REQUIREMENTS_PATH)
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

###############################################################
# Declare all target names that exist for convenience and don't
# represent real paths, which is what Make expects by default:
###############################################################

.PHONY: \
	all \
	black \
	build-release \
	clean \
	dependencies \
	develop \
	push-release \
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
	web
