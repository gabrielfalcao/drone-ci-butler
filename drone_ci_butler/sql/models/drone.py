import json
import io
import requests
import logging
from typing import List, Optional, Any
from chemist import Model, db
from datetime import datetime
from uiclasses import UserFriendlyObject
from drone_ci_butler.drone_api.models import Build, Output
from .base import metadata
from .exceptions import BuildNotFound
from drone_ci_butler.es import connect_to_elasticsearch
from drone_ci_butler.config import config
from drone_ci_butler.util import load_json

es = connect_to_elasticsearch()

logger = logging.getLogger(__name__)


class DroneBuild(Model):
    table = db.Table(
        "drone_build",
        metadata,
        db.Column("id", db.Integer, primary_key=True),
        db.Column("number", db.Integer, nullable=False),
        db.Column("status", db.String(255), nullable=False),
        db.Column("link", db.UnicodeText, nullable=False, index=True),
        db.Column("owner", db.Unicode(255), nullable=False),
        db.Column("repo", db.Unicode(255), nullable=False),
        db.Column("author_login", db.Unicode(255), nullable=False),
        db.Column("author_name", db.Unicode(255)),
        db.Column("author_email", db.Unicode(255)),
        db.Column("drone_api_data", db.UnicodeText),
        db.Column("created_at", db.DateTime),
        db.Column("started_at", db.DateTime),
        db.Column("finished_at", db.DateTime),
        db.Column("updated_at", db.DateTime),
        db.Column("output_retrieved_at", db.DateTime),
        db.Column("last_ruleset_processed_at", db.DateTime),
        db.Column("error_type", db.Unicode(100)),
        db.Column("matches_json", db.UnicodeText),
    )

    def save(self, *args, **kw):
        result = super().save(*args, **kw)

        try:
            es.index(
                f"drone_builds_{config.drone_github_owner}_{config.drone_github_repo}",
                id=self.number,
                body=self.to_document(),
            )
        except Exception:
            pass

        return result

    def to_document(self):
        data = self.to_dict()

        data["matches"] = load_json(data.pop("matches_json", None))
        data["build"] = load_json(data.pop("drone_api_data", None))
        return data

    def update_matches(self, matches: List[UserFriendlyObject]):
        matches_json = json.dumps([m.to_description() for m in matches], default=str)
        return self.update_and_save(
            matches_json=matches_json, last_ruleset_processed_at=datetime.utcnow()
        )

    def drone_api_data_to_dict(self):
        return json.loads(self.drone_api_data)

    def extract_data_from_drone_api(self, owner: str, repo: str, build):
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

        data["drone_api_data"] = json.dumps(build.to_dict())
        return data

    def update_from_drone_api(
        self, owner: str, repo: str, build, output_retrieved_at: datetime = None
    ):
        data = self.extract_data_from_drone_api(owner, repo, build)
        if output_retrieved_at:
            data["output_retrieved_at"] = output_retrieved_at
        return self.update_and_save(**data)

    def is_running(self) -> bool:
        return self.status and self.status == "running"

    def requires_processing(self) -> bool:
        return self.finished_at is None or self.output_retrieved_at is None

    @classmethod
    def get_or_create_from_drone_api(
        cls, owner: str, repo: str, build_number: int, build, update=True
    ):
        stored_build = cls.get_or_create(
            owner=owner,
            repo=repo,
            link=build.link,
            author_login=build.author_login,
            number=build_number,
            status=build.status,
        )
        if update:
            return stored_build.update_from_drone_api(owner, repo, build)
        return stored_build

    def to_drone_api_model(self):
        return Build(**self.drone_api_data_to_dict())


class DroneStep(Model):
    table = db.Table(
        "drone_step",
        metadata,
        db.Column("id", db.Integer, primary_key=True),
        db.Column("stored_build_id", db.Integer, index=True),
        db.Column("build_number", db.Integer, nullable=False),
        db.Column("stage_number", db.Integer, nullable=False),
        db.Column("number", db.Integer, nullable=False),
        db.Column("status", db.String(255)),
        db.Column("exit_code", db.Integer),
        db.Column("output_drone_api_data", db.UnicodeText),
        db.Column("started_at", db.DateTime),
        db.Column("stopped_at", db.DateTime),
        db.Column("updated_at", db.DateTime),
        db.Column("last_notified_at", db.DateTime),
    )

    @classmethod
    def get_or_create_from_drone_api(
        cls,
        owner: str,
        repo: str,
        build_number: int,
        stage_number: int,
        step_number: int,
        output,
    ):
        stored_build = DroneBuild.find_one_by(
            owner=owner,
            repo=repo,
            number=build_number,
        )
        if not stored_build:
            raise BuildNotFound(
                f"Build not found for owner={owner}, repo={repo}, build_number={build_number}"
            )

        stored_step = cls.get_or_create(
            stored_build_id=stored_build.id,
            build_number=build_number,
            stage_number=stage_number,
            number=step_number,
        )
        data = {
            "output_drone_api_data": json.dumps(output.to_dict()),
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
