from uuid import uuid4
from flask import Flask, redirect, url_for, jsonify, session, request
from flask_restx import Api


from drone_ci_butler.version import version
from drone_ci_butler.config import config
from drone_ci_butler.logs import get_logger
from drone_ci_butler.networking import connect_to_elasticsearch
from .core import webapp


es = connect_to_elasticsearch()


logger = get_logger(__name__)


@webapp.route("/session")
def show_session():
    return jsonify(dict(session.items()))


@webapp.route("/hooks/drone", methods=["GET", "POST"])
def drone_webhook():
    data = request.get_json(force=True, silent=True, cache=True)
    logger.info(f"drone webhook invoked")
    if data:
        es.index("drone-webhook", id=str(uuid4()), body=data)

    return jsonify({"ok": True})


@webapp.route("/logout")
def logout():
    session.clear()
    return redirect("/")
