#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ast
import os
from setuptools import setup, find_packages


PACKAGE_NAME = "drone-ci-butler"  # used by "pip install ..."
MODULE_NAME = "drone_ci_butler"  # used by "import ..."
AUTHOR = "Your Name"
AUTHOR_EMAIL = "youremail@example.com"


def local_file(*f):
    with open(os.path.join(os.path.dirname(__file__), *f), "r") as fd:
        return fd.read()


class VersionFinder(ast.NodeVisitor):
    VARIABLE_NAME = "version"

    def __init__(self):
        self.version = None

    def visit_Assign(self, node):
        try:
            if node.targets[0].id == self.VARIABLE_NAME:
                self.version = node.value.s
        except Exception:
            pass


def read_version():
    finder = VersionFinder()
    finder.visit(ast.parse(local_file(MODULE_NAME, "version.py")))
    return finder.version


setup(
    name=PACKAGE_NAME,  # used by pip install ...
    version=read_version(),
    description="some tool",
    long_description=local_file("README.rst"),
    entry_points={
        "console_scripts": [f"{PACKAGE_NAME} = {MODULE_NAME}.cli:entrypoint"]
    },
    packages=find_packages(exclude=["*tests*"]),
    include_package_data=True,
    package_data={
        MODULE_NAME: [
            "README.rst",
            "*.png",
            "*.json",
            "*.rst",
            "docs/*",
            "docs/*/*",
            "migrations/versions/*",
            "migrations/*",
        ]
    },
    package_dir={PACKAGE_NAME: MODULE_NAME},
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    install_requires=local_file("requirements.txt").splitlines(),
)
