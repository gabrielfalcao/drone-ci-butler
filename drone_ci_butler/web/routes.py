from flask_restx import Resource, Api
from drone_ci_butler.sql.models import DroneBuild

from .base import api


@api.route("/drone/builds")
class DroneBuilds(Resource):
    def get(self):
        builds = DroneBuild.all()
        # builds = [b.to_drone_api_model() for b in DroneBuild.all()]

        return [b.to_dict() for b in builds]
