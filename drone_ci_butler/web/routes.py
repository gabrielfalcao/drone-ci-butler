from .base import api
from drone_ci_butler.sql.models import DroneBuild


@api.route("/drone/builds")
class DroneBuilds(Resource):
    def get(self):
        return {"hello": "world"}
