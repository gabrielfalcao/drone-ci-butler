from flask import Flask
from flask_restx import Api

from drone_ci_butler.version import version


SERVER_NAME = f"DroneAPI Butler v{version}"


class Application(Flask):
    def process_response(self, response):
        response.headers["server"] = SERVER_NAME
        super().process_response(response)
        return response


webapp = Flask(__name__)
api = Api(webapp)
