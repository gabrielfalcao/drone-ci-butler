import gevent.monkey

gevent.monkey.patch_all()

import sys
import time
import socket
import logging
import json
import click
import multiprocessing

# enable default event handlers
import drone_ci_butler.default_events

from alembic.config import Config as AlembicConfig
from alembic import command as alembic_command

from gevent.pool import Pool
from typing import Optional
from uiclasses import Model
from pathlib import Path
from datetime import datetime, timedelta
from zmq.devices import ProxySteerable

from drone_ci_butler.version import version
from drone_ci_butler.drone_api import DroneAPIClient, HttpCache
from drone_ci_butler import sql
from drone_ci_butler.slack import SlackClient
from drone_ci_butler.logs import get_logger
from drone_ci_butler.drone_api.models import Build, OutputLine, Step, Stage, Output
from drone_ci_butler.web import webapp
from drone_ci_butler.config import config
from drone_ci_butler.sql.models.slack import SlackMessage
from drone_ci_butler.sql.models.drone import DroneBuild
from drone_ci_butler.workers import GetBuildInfoWorker
from drone_ci_butler.workers import QueueServer, QueueClient, ClientSocketType
from drone_ci_butler.exceptions import ConfigMissing
from drone_ci_butler.es import connect_to_elasticsearch


alembic_ini_path = Path(__file__).parent.joinpath("alembic.ini").absolute()


class Context(Model):

    client: DroneAPIClient
    owner: str
    repo: str


logger = get_logger(__name__)


def entrypoint():
    try:
        main()
    except ConfigMissing as e:
        print_error(f"{e}")
        raise SystemExit(1)


def print_error(message):
    sys.stderr.write(str(message))
    sys.stderr.write("\n")
    sys.stderr.flush()


@click.group()
@click.option("-u", "--drone-url", default=config.drone_url)
@click.option("-t", "--drone-access-token", default=config.drone_access_token)
@click.option("-o", "--owner", default=config.drone_github_owner)
@click.option("-r", "--repo", default=config.drone_github_repo)
@click.pass_context
def main(ctx, drone_url, drone_access_token, owner, repo):
    # if sys.stdout.isatty():
    args = " ".join(sys.argv[1:])
    sys.stderr.write(
        f"\033[0;1;32mDroneCI Butler \033[0;1mv{version}\033[0;1;36m {args}\033[0m\n"
    )
    sys.stderr.flush()
    ctx.obj = {
        "drone_url": drone_url,
        "access_token": drone_access_token,
        "github_owner": owner,
        "github_repo": repo,
    }


@main.command("check")
def healthcheck():
    print("Python modules were installed properly 🎉\n")


@main.command("slack")
def slack_test():
    client = SlackClient()  # (token=config.SLACK_APP_USER_TOKEN)
    app_client = SlackClient(token=config.SLACK_APP_USER_TOKEN)

    # message_response = client.chat_postMessage(
    #     channel="#drone-ci-butler", text="Hello from your app! :tada:"
    # )
    # client.chat_delete(channel=channel, ts=message_response.data["ts"])

    # channel_response = client.conversations_info(
    #     channel=channel, include_num_members=True
    # )
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🔴 Build failed for the PR 13355 nytm/wf-project",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "something went wrong :oops:"},
        },
        {"type": "divider"},
    ]

    channel = "C023Z62N59Q"
    user_id = "W01BD07TYGP"
    bot_user_id = "U024G7WKBL6"

    conversations = client.get_user_conversations()

    stored_messages = SlackMessage.all()
    for m in stored_messages:
        msg = json.loads(m.message)
        logger.warning(f"deleting message: {m.get('text', m.id)}")
        client.delete_message(channel_id=msg["channel"], ts=msg["ts"])


@main.command("web")
@click.option("-H", "--host", default=config.web_host)
@click.option("-P", "--port", default=config.web_port, type=int)
@click.option("-D", "--debug", is_flag=True)
@click.pass_context
def web(ctx, host, port, debug):
    sql.setup_db()
    webapp.run(debug=debug, port=port, host=host)


@main.command("workers")
@click.option("-r", "--queue-rep-address", default=config.worker_queue_rep_address)
@click.option("-p", "--queue-pull-address", default=config.worker_queue_pull_address)
@click.option("-m", "--max-workers", default=config.max_workers_per_process, type=int)
@click.pass_context
def workers(ctx, queue_rep_address, queue_pull_address, max_workers):
    sql.setup_db()
    if max_workers < 2:
        logger.error(f"{' '.join(sys.argv)}")
        logger.error(f"the setting -m/--max-workers cannot be lower than 2")
        raise SystemExit(1)

    pool_size = max_workers

    pool = Pool(pool_size)
    queue_server = QueueServer(
        queue_rep_address, queue_pull_address, "inproc://build-info"
    )

    pool.spawn(queue_server.run)
    pool.join(1, raise_error=True)

    for worker_id in range(pool_size - 1):  # the +1 from pool_size
        build_info_worker = GetBuildInfoWorker(
            "inproc://build-info",
            worker_id,
        )
        pool.spawn(build_info_worker.run)

    while True:
        try:
            pool.join(1, raise_error=True)
        except KeyboardInterrupt:
            pool.kill()
            raise SystemExit(1)


@main.command("worker:get_build_info")
@click.option("-c", "--pull-connect-address", default=config.worker_push_address)
@click.pass_context
def worker_get_build_info(ctx, pull_connect_address):
    sql.setup_db()
    worker = GetBuildInfoWorker(pull_connect_address)
    worker.run()


@main.command("queue")
@click.option("-s", "--pull-bind-address", default=config.worker_pull_address)
@click.option("-p", "--push-bind-address", default=config.worker_push_address)
@click.option("-P", "--pub-bind-address", default=config.worker_monitor_address)
@click.option("-C", "--control-bind-address", default=config.worker_control_address)
@click.pass_context
def worker_queue(
    ctx, pull_bind_address, push_bind_address, pub_bind_address, control_bind_address
):
    sql.setup_db()
    device = ProxySteerable(
        frontend=zmq.PULL, backend=zmq.PUSH, capture=zmq.PUB, control=zmq.PULL
    )
    device.bind_in(pull_bind_address)
    device.bind_out(push_bind_address)
    device.bind_mon(pub_bind_address)
    device.bind_ctrl(control_bind_address)
    device.run()


@main.command("builds")
@click.option("-p", "--initial-page", default=config.drone_api_initial_page, type=int)
@click.option("-P", "--max-pages", default=config.drone_api_max_pages, type=int)
@click.option("-m", "--max-builds", default=config.drone_api_max_builds, type=int)
@click.option("-c", "--connect-address", default=config.worker_queue_pull_address)
@click.pass_context
def get_builds(ctx, initial_page, connect_address, max_builds, max_pages):
    sql.setup_db()
    client = DroneAPIClient(
        ctx.obj["drone_url"],
        ctx.obj["access_token"],
        max_builds=max_builds,
        max_pages=max_pages,
    )

    worker = QueueClient(connect_address, socket_type=ClientSocketType.PUSH)
    worker.connect()

    for builds, page, total_pages in client.iter_builds_by_page(
        owner=ctx.obj["github_owner"], repo=ctx.obj["github_repo"], page=initial_page
    ):
        try:
            count = len(builds)
            logger.info(
                f"enqueing the {count} builds found (page {page}/{total_pages})"
            )

            for i, build in enumerate(builds, start=1):
                logger.debug(
                    f"enqueing {build.link} (#{build.number} by {build.author_login})"
                )
                worker.send({"build_id": build.number, "ignore_filters": True})
        except Exception as e:
            logger.error(f"failed to process builds")
            worker.close()
            gevent.sleep(1)
            worker.connect()
        finally:
            # worker.close()
            pass

    worker.close()


@main.command("env")
@click.option("-d", "--docker", is_flag=True)
@click.pass_context
def print_env_declaration(ctx, docker):
    if docker:
        print(config.to_docker_env_declaration())
    else:
        print(config.to_shell_env_declaration())


def check_db_connection(engine):
    url = engine.url
    logger.info(f"Trying to connect to DB: {str(url)!r}")
    result = engine.connect()
    logger.info(f"SUCCESS: {url}")
    result.close()


def check_database_dns():
    try:
        logger.info(f"Check ability to resolve name: {config.database_hostname}")
        host = socket.gethostbyname(config.database_hostname)
        logger.info(f"SUCCESS: {config.database_hostname!r} => {host!r}")
    except Exception as e:
        return e

    if not config.database_port:
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        logger.info(f"Checking TCP connection to {host!r}")
        sock.connect((host, config.database_port))
        logger.info(f"SUCCESS: TCP connection to database works!!")
    except Exception as e:
        return e
    finally:
        sock.close()


@main.command("migrate-db")
@click.option("--target", default="head")
@click.option("--alembic-ini", default=alembic_ini_path)
@click.pass_context
def migrate_db(ctx, target, alembic_ini):
    "runs the migrations"

    error = check_database_dns()
    if error:
        logger.error(f"could not resolve {config.database_hostname!r}: {error}")
        raise SystemExit(1)

    alembic_ini_path = Path(alembic_ini).expanduser().absolute()
    alembic_cfg = AlembicConfig(str(alembic_ini_path))
    alembic_cfg.set_section_option("alembic", "sqlalchemy.url", config.sqlalchemy_uri)
    alembic_cfg.set_section_option(
        "alembic",
        "script_location",
        str(alembic_ini_path.parent.joinpath("migrations")),
    )
    alembic_command.upgrade(alembic_cfg, target)


@main.command("index")
def index_builds_elasticsearch():
    sql.setup_db()
    es = connect_to_elasticsearch()
    owner = config.drone_github_owner
    repo = config.drone_github_repo
    get_logger("elasticsearch").setLevel(logging.INFO)
    for build in DroneBuild.all():
        es.index(
            f"drone_builds_{owner}_{repo}", id=build.number, body=build.to_document()
        )


@main.command("purge")
@click.option("--elasticsearch", is_flag=True)
@click.option("--http-cache", is_flag=True)
def purge_es_and_cache(elasticsearch, http_cache):
    es_indexes = ["drone*", "*-webhooks"]

    if not elasticsearch and not http_cache:
        print_error(f"you must provide either --elasticsearch or --http-cache")
        raise SystemExit(1)

    if elasticsearch:
        print(f"deleting elasticsearch indexes: {es_indexes}")
        es = connect_to_elasticsearch()
        get_logger("elasticsearch").setLevel(logging.INFO)
        for index in es_indexes:
            try:
                es.indices.delete(index=index, ignore=[400, 404])
            except Exception as e:
                logger.warning(f'failed to purge index "{index}": {e}')

        get_logger("elasticsearch").setLevel(logging.WARNING)

    else:
        logger.warning(
            f"provide --elasticsearch if you want to delete the indexes: {es_indexes}"
        )

    if http_cache:
        sql.setup_db()
        http_cache_count = HttpCache.count()
        if http_cache_count > 0:
            print("deleting http cache")
            HttpCache.purge()

    else:
        logger.warning(f"provide --http-cache if you want to delete ")
