import gevent.monkey

gevent.monkey.patch_all()

import time
import click
from gevent.pool import Pool
from typing import Optional
from uiclasses import Model
from pathlib import Path
from datetime import datetime, timedelta
from drone_ci_butler.drone_api import DroneAPIClient
from drone_ci_butler import sql
from drone_ci_butler.logs import logger
from drone_ci_butler.drone_api.models import Build, OutputLine, Step, Stage, Output

from drone_ci_butler.workers import GetBuildInfoWorker
from drone_ci_butler.workers import QueueServer, QueueClient

DEFAULT_QUEUE_ADDRESS = "tcp://127.0.0.1:5000"
DEFAULT_PUSH_ADDRESS = "tcp://127.0.0.1:6000"


class Context(Model):

    client: DroneAPIClient
    owner: str
    repo: str


@click.group()
@click.option("-t", "--drone-access-token", default="VIiQwPXd3YdxtAzkjl1S7rUUxaQh9PMy")
@click.option("-u", "--drone-url", default="https://drone.dv.nyt.net/")
@click.option("-o", "--owner", default="nytm")
@click.option("-r", "--repo", default="wf-project-vi")
@click.pass_context
def main(ctx, drone_access_token, drone_url, owner, repo):
    print("DroneCI Butler")
    sql.context.set_default_uri(
        "postgresql://drone_ci_butler@localhost/drone_ci_butler"
    )
    ctx.obj = {
        "drone_url": drone_url,
        "access_token": drone_access_token,
        "github_owner": owner,
        "github_repo": repo,
    }


@main.command("workers")
@click.option("-s", "--queue-address", default=DEFAULT_QUEUE_ADDRESS)
@click.option("-m", "--max-workers", default=2, type=int)
@click.pass_context
def workers(ctx, queue_address, max_workers):
    pool = Pool()
    queue_server = QueueServer(queue_address, "inproc://build-info")

    pool.spawn(queue_server.run)
    for worker_id in range(max_workers):
        build_info_worker = GetBuildInfoWorker(
            "inproc://build-info", worker_id, **ctx.obj
        )
        pool.spawn(build_info_worker.run)

    while True:
        try:
            pool.join(1)
        except KeyboardInterrupt:
            pool.kill()
            raise SystemExit(1)


@main.command("worker:get_build_info")
@click.option("-c", "--pull-connect-address", default=DEFAULT_PUSH_ADDRESS)
@click.pass_context
def worker_get_build_info(ctx, pull_connect_address):
    worker = GetBuildInfoWorker(pull_connect_address)
    worker.run()


@main.command("worker:queue")
@click.option("-s", "--rep-bind-address", default=DEFAULT_QUEUE_ADDRESS)
@click.option("-p", "--push-bind-address", default=DEFAULT_PUSH_ADDRESS)
@click.pass_context
def worker_queue(ctx, rep_bind_address, push_bind_address):
    worker.run()


@main.command("builds")
@click.option("-d", "--days", default=5, type=int)
@click.option("-c", "--rep-connect-address", default=DEFAULT_QUEUE_ADDRESS)
@click.pass_context
def get_builds(ctx, rep_connect_address, days):
    client = DroneAPIClient(
        url=ctx.obj["drone_url"],
        access_token=ctx.obj["access_token"],
    )
    builds = client.get_builds(ctx.obj["github_owner"], ctx.obj["github_repo"])
    builds = builds.filter(
        lambda b: b.finished_at > datetime.utcnow() - timedelta(days=days)
    )
    count = len(builds)
    print(f"found {count} failed builds in the last {days} days")
    for i, build in enumerate(builds, start=1):
        worker = QueueClient(rep_connect_address)
        worker.connect()
        print(
            f" -> enqueing build {i} of {count} for output analysis (#{build.number} by {build.author_login})"
        )
        worker.send({"build_id": build.number})
        worker.close()
    return


@click.option("-f", "--filter-status", default="failure")
def filter_builds(builds):
    if filter_status:
        builds = builds.filter(
            lambda build: build.status != filter_status and build.sender
        )

    for build in builds:
        build = ctx.obj.client.get_build_with_logs(
            ctx.obj.owner, ctx.obj.repo, build.number
        )
        failed_steps = build.failed_steps()
        finished = datetime.fromtimestamp(build.finished)
        status_color = build.status == "success" and "\033[1;32m" or "\033[1;31m"
        if len(failed_steps) == 0:
            continue
        print(
            f"Build {status_color}{build.number}\033[0m by \033[1;37m{build.author_name or build.sender} <{build.author_email or build.sender}> {status_color}{build.status}\033[1;37m at {finished}\033[0m"
        )
        for step in failed_steps:
            output = step.to_string(prefix="             ")

            if output:
                print(
                    f"         In Step: \033[1;33m{step.name} ({step.number}) failed with code {step.exit_code}\033[0m"
                )
                print(f"\033[1;31m{output}\033[0m")
