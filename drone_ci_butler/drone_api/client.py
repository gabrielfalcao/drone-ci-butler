import logging
from urllib.parse import urljoin
from pathlib import Path
from datetime import datetime, timedelta
from requests import Response, Session
from drone_ci_butler import events
from drone_ci_butler.logs import get_logger
from drone_ci_butler.version import version
from drone_ci_butler.drone_api.models import Build, OutputLine, Output
from drone_ci_butler.drone_api.cache import HttpCache

from drone_ci_butler.drone_api.exceptions import invalid_response, ClientError

logger = get_logger(__name__)

ALLOWED_GITHUB_USERS = (
    "Emmawaterman",
    "caiogondim",
    "coolov",
    "delambo",
    "fesebuv",
    "gabrielfalcao",
    "ilyaGurevich",
    "iocedano",
    "kmnaid",
    "marzagao",
    "montmanu",
    "staylor",
    "woodb",
)


class DroneAPIClient(object):
    def __init__(
        self, url: str, access_token: str, max_pages: int = 100, max_builds: int = 100
    ):
        self.api_url = url
        self.access_token = access_token
        self.http = Session()
        self.http.headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": f"DroneCI Butler v{version}",
        }
        self.max_pages = max_pages
        self.max_builds = max_builds
        self.cache = HttpCache()

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
        # print(f'\033[1;31mcache miss \033[2m{method} {path}\033[0m')
        return interaction.response()

    def get_builds(
        self, owner: str, repo: str, limit=10000, page=1, count=0
    ) -> Build.List:
        logger.info(f"Retrieving builds for {owner}/{repo} page {page}")
        result = self.request(
            "GET",
            f"/api/repos/{owner}/{repo}/builds",
            params={"page": page, "limit": limit},
            skip_cache=True,
        )
        builds = Build.List(
            map(
                lambda build: build.with_headers(result.headers),
                Build.List(result.json()),
            )
            # running and failed pull-requests only
        ).filter(
            lambda build: "/pull/" in build.link
            and build.status == "failure"
            # and build.status in ("running", "failure")
            # and build.author_login in ALLOWED_GITHUB_USERS
        )
        events.get_builds.send(
            self, owner=owner, repo=repo, limit=limit, page=page, builds=builds
        )
        total_builds = len(builds) + count
        if total_builds < self.max_builds and page < self.max_pages:
            logger.info(f"total builds: {total_builds}")
            next_page = self.get_builds(
                owner, repo, limit, page + 1, count=total_builds
            )
            if next_page:
                builds.extend(next_page)

        return Build.List(builds.sorted(key=lambda b: b.updated, reverse=True)[:self.max_builds])

    def get_build_info(self, owner: str, repo: str, build_id: str) -> Build:
        result = self.request("GET", f"/api/repos/{owner}/{repo}/builds/{build_id}")
        build = Build(result.json()).with_headers(result.headers)
        events.get_build_info.send(
            self, owner=owner, repo=repo, build_id=build_id, build=build
        )
        return build

    def get_build_step_output(
        self, owner: str, repo: str, build_id: int, stage: int, step: int
    ) -> OutputLine.List:
        result = self.request(
            "GET", f"/api/repos/{owner}/{repo}/builds/{build_id}/logs/{stage}/{step}"
        )
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
            build_id=build_id,
            stage=stage,
            step=step,
            output=output,
        )
        return output

    def get_latest_build(self, owner: str, repo: str, branch: str):
        result = self.request(
            "GET", f"/api/repos/{owner}/{repo}/builds/latest", params={"branch": branch}
        )
        build = Build(result.json()).with_headers(result.headers)
        return self.inject_logs_into_build(owner, repo, build)

    def inject_logs_into_build(self, owner: str, repo: str, build: Build):
        def inject_logs(build):
            for stage in build.stages or []:
                stage = stage.with_build(build)
                for step in stage.steps or []:
                    step = step.with_stage(stage)
                    try:
                        output = self.get_build_step_output(
                            owner=owner,
                            repo=repo,
                            build_id=build.number,
                            stage=stage.number,
                            step=step.number,
                        )
                    except ClientError as e:
                        logger.debug(
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

    def close(self):
        self.http.close()

    def __del__(self):
        self.close()
