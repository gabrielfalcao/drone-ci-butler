from flask import Flask, redirect, url_for
from flask_restx import Api

from slack import WebClient
from slack.errors import SlackApiError

from drone_ci_butler.version import version
from drone_ci_butler.config import config
from .core import Application


webapp = Application()
api = webapp.api
oauth = webapp.oauth
cors = webapp.cors
session = webapp.session
