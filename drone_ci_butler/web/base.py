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


@webapp.route("/hooks/<service_name>", methods=["GET", "POST"])
@webapp.route("/hooks/<service_name>/<path:path>", methods=["GET", "POST"])
def service_webhook(service_name, path=None):
    body = request.get_json(force=True, silent=True, cache=True)

    data = {
        "body": dict(body),
        "service_name": service_name,
        "headers": dict(request.headers),
    }
    if path:
        data["path"] = path

    logger.info(f"{service_name} webhook invoked", extra=data)
    if data:
        es.index(f"{service_name}-webhook", id=str(uuid4()), body=data)

    return jsonify({"ok": True})


@webapp.route("/logout")
def logout():
    session.clear()
    return redirect("/")
