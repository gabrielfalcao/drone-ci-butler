import click
from typing import Optional
from uiclasses import Model
from pathlib import Path
from datetime import datetime
from drone_ci_butler.drone_api import DroneAPIClient

class Context(Model):

    client: DroneAPIClient
    owner: str
    repo: str


@click.group()
@click.option('-C', '--cache-name')
@click.option('-o', '--owner', default='nytm')
@click.option('-r', '--repo', default='wf-project-vi')
@click.pass_context
def main(ctx, cache_name, owner, repo):
    print("DroneCI Butler")
    ctx.obj = Context()
    ctx.obj.client=DroneAPIClient(
        url="https://drone.dv.nyt.net/api/user",
        access_token="VIiQwPXd3YdxtAzkjl1S7rUUxaQh9PMy",
        sqlite_cache_file=Path(".").absolute().joinpath("api-cache.sqlite"),
    )
    ctx.obj.owner=owner
    ctx.obj.repo=repo



@main.command('builds')
@click.option('-f', '--filter-status', default='failure')
@click.pass_context
def get_builds(ctx, filter_status):
    builds = ctx.obj.client.get_builds(ctx.obj.owner, ctx.obj.repo)

    if filter_status:
        builds = builds.filter(lambda build: build.status != filter_status and build.sender)

    for build in builds:
        build = ctx.obj.client.get_build_with_logs(ctx.obj.owner, ctx.obj.repo, build.number)
        failed_steps = build.failed_steps()
        finished = datetime.fromtimestamp(build.finished)
        status_color = build.status == 'success' and '\033[1;32m' or '\033[1;31m'
        if len(failed_steps) == 0:
            continue
        print(f'Build {status_color}{build.number}\033[0m by \033[1;37m{build.author_name or build.sender} <{build.author_email or build.sender}> {status_color}{build.status}\033[1;37m at {finished}\033[0m')
        for step in failed_steps:
            output = step.to_string(prefix='             ')


            if output:
                print(f'         In Step: \033[1;33m{step.name} ({step.number}) failed with code {step.exit_code}\033[0m')
                print(f'\033[1;31m{output}\033[0m')
