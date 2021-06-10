from flask import Flask, redirect, url_for, jsonify, session
from flask_restx import Api

from slack import WebClient
from slack.errors import SlackApiError

from drone_ci_butler.version import version
from drone_ci_butler.config import config
from .core import webapp


@webapp.route("/session")
def show_session():
    return jsonify(dict(session.items()))


@webapp.route("/logout")
def logout():
    session.clear()
    return redirect("/")
