import logging
from urllib.parse import urljoin
from pathlib import Path
from requests import Response, Session
from drone_ci_butler.version import version
from drone_ci_butler.drone_api.models import Build, OutputLine, Output
from drone_ci_butler.drone_api.cache import HttpCache

from drone_ci_butler.drone_api.exceptions import invalid_response, ClientError

logger = logging.getLogger(__name__)


class DroneAPIClient(object):
    def __init__(self, url: str, access_token: str):
        self.api_url = url
        self.access_token = access_token
        self.http = Session()
        self.http.headers = {
            "Authorization": f"Bearer {access_token}",
            "User-Agent": f"DroneCI Butler v{version}",
        }
        self.cache = HttpCache()

    def make_url(self, path) -> str:
        return urljoin(self.api_url, path)

    def request(self, method: str, path: str, data=None, headers=None, **kwargs):
        url = self.make_url(path)
        headers = headers or {}
        interaction = self.cache.get_by_url_and_method(method=method, url=url)
        if interaction and interaction.response:
            # print(f'\033[1;34mcache hit \033[2m{method} {path}\033[0m')
            return interaction.response()

        response = self.http.request(method, url, data=data, headers=headers, **kwargs)
        if response.status_code != 200:
            raise invalid_response(response)

        interaction = self.cache.set(response.request, response)
        # print(f'\033[1;31mcache miss \033[2m{method} {path}\033[0m')
        return interaction.response()

    def get_builds(self, owner: str, repo: str, limit=10000, page=1) -> Build.List:
        result = self.request(
            "GET",
            f"/api/repos/{owner}/{repo}/builds",
            params={"page": page, "limit": limit},
        )
        return Build.List(
            map(
                lambda build: build.with_headers(result.headers),
                Build.List(result.json()),
            )
        )

    def get_build_info(self, owner: str, repo: str, build_id: str) -> Build:
        result = self.request("GET", f"/api/repos/{owner}/{repo}/builds/{build_id}")
        build = Build(result.json())
        return build.with_headers(result.headers)

    def get_build_step_output(
        self, owner: str, repo: str, build_id: int, stage: int, step: int
    ) -> OutputLine.List:
        result = self.request(
            "GET", f"/api/repos/{owner}/{repo}/builds/{build_id}/logs/{stage}/{step}"
        )
        data = result.json()
        if isinstance(data, dict):
            return Output(items).with_headers(result.headers)

        elif isinstance(data, list):
            return Output({"lines": data}).with_headers(result.headers)
        else:
            raise ClientError(
                response, f"unexpected step log output type: {type(data)} {step}"
            )

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

                    step = step.with_output(output).with_stage(stage)
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
