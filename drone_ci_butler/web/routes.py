from flask import Response
from flask_restx import Resource, Api
from drone_ci_butler.sql.models import DroneBuild, SlackMessage, User, AccessToken

from .core import api

drone = api.namespace(
    "Drone",
    path="/drone",
    description="Retrieve processed Drone builds",
)

mgmt = api.namespace(
    "Management API",
    path="/mgmt",
    description="Manage Users and Settings",
)


@drone.route("/builds", endpoint="Drone Builds")
class DroneBuilds(Resource):
    def get(self):
        builds = DroneBuild.all()
        # builds = [b.to_drone_api_model() for b in DroneBuild.all()]

        return [b.to_dict() for b in builds]


@mgmt.route("/users", endpoint="Users")
class Users(Resource):
    def get(self):
        return [u.to_dict() for u in User.all()]


@mgmt.route("/user/<int:user_id>", endpoint="User Info")
class UserInfo(Resource):
    def get(self, user_id):
        user = User.find_one_by(id=user_id)
        if user:
            return user.to_dict()

        return Response(status=404, headers={"Content-Type": "application/json"})


@mgmt.route("/slack/messages", endpoint="Slack Messages")
class SlackMessages(Resource):
    def get(self):
        return [s.to_dict() for s in SlackMessages.all()]
