import json
import io
import requests
from chemist import Model, db
from datetime import datetime
from drone_ci_butler.drone_api.models import Build, Output
from .base import metadata
from .exceptions import BuildNotFound


class DroneBuild(Model):
    table = db.Table(
        "drone_build",
        metadata,
        db.Column("id", db.Integer, primary_key=True),
        db.Column("build_id", db.Integer, nullable=False),
        db.Column("number", db.Integer, nullable=False),
        db.Column("status", db.String(255), nullable=False),
        db.Column("link", db.UnicodeText, nullable=False, index=True),
        db.Column("owner", db.Unicode(255), nullable=False),
        db.Column("repo", db.Unicode(255), nullable=False),
        db.Column("author_login", db.Unicode(255), nullable=False),
        db.Column("author_name", db.Unicode(255)),
        db.Column("author_email", db.Unicode(255)),
        db.Column("json_data", db.UnicodeText),
        db.Column("created_at", db.DateTime),
        db.Column("started_at", db.DateTime),
        db.Column("finished_at", db.DateTime),
        db.Column("updated_at", db.DateTime),
    )

    def json_data_to_dict(self):
        return json.loads(self.json_data)

    def extract_data_from_drone_api(self, owner: str, repo: str, build: Build):
        data = {}
        if build.status:
            data["status"] = build.status
        if build.author_login:
            data["author_login"] = build.author_login
        if build.author_email:
            data["author_email"] = build.author_email
        if build.author_name:
            data["author_name"] = build.author_name

        data["status"] = build.status
        data["link"] = build.link

        if build.created:
            data["created_at"] = datetime.fromtimestamp(build.created)
        if build.started:
            data["started_at"] = datetime.fromtimestamp(build.started)
        if build.finished:
            data["finished_at"] = datetime.fromtimestamp(build.finished)
        if build.updated:
            data["updated_at"] = datetime.fromtimestamp(build.updated)

        data["json_data"] = json.dumps(build.to_dict())
        return data

    def update_from_drone_api(self, owner: str, repo: str, build: Build):
        data = self.extract_data_from_drone_api(owner, repo, build)
        return self.update_and_save(**data)

    @classmethod
    def get_or_create_from_drone_api(
        cls, owner: str, repo: str, build: Build, update=True
    ):
        stored_build = cls.get_or_create(
            owner=owner,
            repo=repo,
            build_id=build.id,
            link=build.link,
            author_login=build.author_login,
            number=build.number,
            status=build.status,
        )
        if update:
            return stored_build.update_from_drone_api(owner, repo, build)
        return stored_build

    def to_drone_api_model(self) -> Build:
        return Build(**self.json_data_to_dict())


class DroneStep(Model):
    table = db.Table(
        "drone_step",
        metadata,
        db.Column("id", db.Integer, primary_key=True),
        db.Column("stored_build_id", db.ForeignKey("drone_step.id")),
        db.Column("build_number", db.Integer, nullable=False),
        db.Column("stage_number", db.Integer, nullable=False),
        db.Column("number", db.Integer, nullable=False),
        db.Column("status", db.String(255)),
        db.Column("exit_code", db.Integer),
        db.Column("output_json_data", db.UnicodeText),
        db.Column("started_at", db.DateTime),
        db.Column("stopped_at", db.DateTime),
        db.Column("updated_at", db.DateTime),
    )

    @classmethod
    def get_or_create_from_drone_api(
        cls,
        owner: str,
        repo: str,
        build_number: int,
        stage_number: int,
        step_number: int,
        output: Output,
    ):
        stored_build = DroneBuild.find_one_by(
            owner=owner,
            repo=repo,
            number=build_number,
        )
        if not stored_build:
            # import ipdb;ipdb.set_trace()  # fmt: skip
            raise BuildNotFound(
                f"Build not found for owner={owner}, repo={repo}, build_id={build_id}"
            )
        stored_step = cls.get_or_create(
            stored_build_id=stored_build.id,
            build_number=build_number,
            stage_number=stage_number,
            number=step_number,
        )

        data = {
            "output_json_data": json.dumps(output.to_dict()),
        }
        build = stored_build.to_drone_api_model()
        step = build.get_step_by_number(step_number)
        if step.exit_code:
            data["exit_code"] = step.exit_code
        if step.status:
            data["status"] = step.status

        if step.started_at:
            data["started_at"] = step.started_at
        if step.stopped_at:
            data["stopped_at"] = step.stopped_at

        return stored_step.update_and_save(**data)
