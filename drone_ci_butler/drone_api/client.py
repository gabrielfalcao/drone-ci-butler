import logging
from redis import Redis
from urllib.parse import urljoin
from pathlib import Path
from typing import NoReturn, Optional, Type, TypeVar

from datetime import datetime, timedelta
from requests import Response, Session
from drone_ci_butler import events
from drone_ci_butler.logs import get_logger
from drone_ci_butler.config import Config, config
from drone_ci_butler.version import version
from drone_ci_butler.drone_api.models import Build, OutputLine, Output
from drone_ci_butler.drone_api.cache import HttpCache

from drone_ci_butler.drone_api.exceptions import invalid_response, ClientError, NotFound

logger = get_logger(__name__)

# ALLOWED_GITHUB_USERS = (
#     "Emmawaterman",
#     "caiogondim",
#     "coolov",
#     "delambo",
#     "fesebuv",
#     "gabrielfalcao",
#     "ilyaGurevich",
#     "iocedano",
#     "kmnaid",
#     "marzagao",
#     "montmanu",
#     "staylor",
#     "woodb",
# )

DroneAPIClient = TypeVar("DroneAPIClient")


class DroneAPIClient(object):
    def __init__(
        self,
        url: str = config.drone_url,
        access_token: str = config.drone_access_token,
        max_pages: int = config.drone_api_max_pages,
        max_builds: int = config.drone_api_max_builds,
        owner: str = config.drone_github_owner,
        repo: str = config.drone_github_repo,
    ):
        self.api_url = url
        self.access_token = access_token
        self.http = Session()
        self.http.headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": f"DroneCI Butler v{version}",
        }
        self.max_pages = max_pages
        self.owner = owner
        self.repo = repo
        self.max_builds = max_builds
        self.cache = HttpCache()
        self.redis = Redis

    @classmethod
    def from_config(cls: DroneAPIClient, config: Config) -> DroneAPIClient:
        return cls(
            config.drone_url,
            config.drone_access_token,
            max_builds=config.drone_api_max_builds,
            max_pages=config.drone_api_max_pages,
            owner=config.drone_api_owner,
            repo=config.drone_api_repo,
        )

    def make_url(self, path) -> str:
        return urljoin(self.api_url, path)

    def request(
        self,
        method: str,
        path: str,
        data=None,
        headers=None,
        skip_cache: bool = False,
        **kwargs,
    ):
        url = self.make_url(path)
        headers = headers or {}
        if not skip_cache:
            interaction = self.cache.get_by_url_and_method(method=method, url=url)
            if interaction and interaction.response:
                # print(f'\033[1;34mcache hit \033[2m{method} {path}\033[0m')
                return interaction.response()

        response = self.http.request(method, url, data=data, headers=headers, **kwargs)
        if response.status_code != 200:
            raise invalid_response(response)

        if skip_cache:
            return response

        interaction = self.cache.set(response.request, response)
        return interaction.response()

    def get_builds(
        self,
        owner: str = None,
        repo: str = None,
        limit=10000,
        page=0,
        count=0,
        max_pages: int = None,
    ) -> Build.List:
        owner = owner or self.owner
        repo = repo or self.repo

        result = self.request(
            "GET",
            f"/api/repos/{owner}/{repo}/builds",
            params={"page": page, "limit": limit},
            skip_cache=True,
        )
        all_builds = Build.List(result.json())
        max_pages = max_pages or self.max_pages + page
        builds = Build.List(
            map(
                lambda build: build.with_headers(result.headers),
                all_builds,
            )
        )
        events.get_builds.send(
            self,
            owner=owner,
            repo=repo,
            limit=limit,
            page=page,
            builds=all_builds,
            max_builds=self.max_builds,
            max_pages=max_pages,
        )

        total_builds = len(builds) + count
        logger.debug(f"Retrieved {total_builds} builds for {owner}/{repo} page {page}")
        if total_builds < self.max_builds and page < max_pages:
            next_page = self.get_builds(
                owner, repo, limit, page + 1, count=total_builds, max_pages=max_pages
            )
            if next_page:
                builds.extend(next_page)

        all_builds = Build.List(
            builds.sorted(key=lambda b: b.finished or b.updated, reverse=True)
        )

        for build in all_builds:
            events.get_build_info.send(
                self, owner=owner, repo=repo, build_number=build.number, build=build
            )
        return all_builds

    def iter_builds_by_page(
        self,
        owner: str,
        repo: str,
        limit=10000,
        page=0,
        count=0,
        max_pages=None,
    ) -> Build.List:
        owner = owner or self.owner
        repo = repo or self.repo
        result = self.request(
            "GET",
            f"/api/repos/{owner}/{repo}/builds",
            params={"page": page, "limit": limit},
            skip_cache=True,
        )
        all_builds = Build.List(result.json())
        max_pages = max_pages or self.max_pages + page
        builds = Build.List(
            map(
                lambda build: build.with_headers(result.headers),
                all_builds,
            )
        )
        yield builds, page, max_pages
        events.iter_builds_by_page.send(
            self,
            owner=owner,
            repo=repo,
            limit=limit,
            page=page,
            builds=all_builds,
            max_builds=self.max_builds,
            max_pages=max_pages,
        )

        total_builds = len(builds) + count
        logger.debug(f"Retrieved {total_builds} builds for {owner}/{repo} page {page}")
        if total_builds < self.max_builds and page < max_pages:
            yield from self.iter_builds_by_page(
                owner, repo, limit, page + 1, count=total_builds, max_pages=max_pages
            )

    def get_build_info(self, owner: str, repo: str, build_number: str) -> Build:
        owner = owner or self.owner
        repo = repo or self.repo
        result = self.request("GET", f"/api/repos/{owner}/{repo}/builds/{build_number}")
        build = Build(result.json()).with_headers(result.headers)
        events.get_build_info.send(
            self, owner=owner, repo=repo, build_number=build_number, build=build
        )
        return build

    def get_build_step_output(
        self,
        owner: str,
        repo: str,
        build_number: int,
        stage_number: int,
        step_number: int,
    ) -> Optional[Output]:
        owner = owner or self.owner
        repo = repo or self.repo
        try:
            result = self.request(
                "GET",
                f"/api/repos/{owner}/{repo}/builds/{build_number}/logs/{stage_number}/{step_number}",
            )
        except NotFound as e:
            logger.error(
                f"failed to retrieve drone step output of build {build_number}: {e}"
            )
            return
        data = result.json()

        if isinstance(data, dict):
            output = Output(items).with_headers(result.headers)

        elif isinstance(data, list):
            output = Output({"lines": data}).with_headers(result.headers)
        else:
            raise ClientError(
                response, f"unexpected step log output type: {type(data)} {step}"
            )

        events.get_build_step_output.send(
            self,
            owner=owner,
            repo=repo,
            build_number=build_number,
            stage_number=stage_number,
            step_number=step_number,
            output=output,
        )
        return output

    def get_latest_build(self, owner: str, repo: str, branch: str):
        owner = owner or self.owner
        repo = repo or self.repo
        result = self.request(
            "GET", f"/api/repos/{owner}/{repo}/builds/latest", params={"branch": branch}
        )
        build = Build(result.json()).with_headers(result.headers)
        events.get_build_info.send(
            self, owner=owner, repo=repo, build_number=build.number, build=build
        )
        build = self.inject_logs_into_build(owner, repo, build)
        return build

    def inject_logs_into_build(self, owner: str, repo: str, build: Build):
        def inject_logs(build):
            for stage in build.stages or []:
                stage = stage.with_build(build)
                for step in stage.steps or []:
                    step = step.with_stage(stage)
                    if step.status == "skipped":
                        continue
                    try:
                        output = self.get_build_step_output(
                            owner=owner,
                            repo=repo,
                            build_number=build.number,
                            stage_number=stage.number,
                            step_number=step.number,
                        )
                    except ClientError as e:
                        logger.error(
                            f"failed to retrieve logs for {owner}/{repo}/logs/{build.number}/{stage}/{step}",
                            e,
                        )
                        continue

                    step = step.with_output(output)
                stage = stage.with_build(build)
            return build

        return inject_logs(build)

    def get_build_with_logs(self, owner: str, repo: str, build_id: str) -> Build.List:
        info = self.get_build_info(owner, repo, build_id)
        return self.inject_logs_into_build(owner, repo, info)

    def close(self) -> NoReturn:
        self.http.close()

    def __del__(self):
        self.close()
