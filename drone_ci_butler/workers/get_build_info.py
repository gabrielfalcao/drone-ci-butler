import gevent
import zmq.green as zmq
from collections import defaultdict

from drone_ci_butler.logs import get_logger
from drone_ci_butler.drone_api import DroneAPIClient

from .base import context


logger = get_logger('build-info-retriever')


class GetBuildInfoWorker(object):
    def __init__(
        self,
        pull_connect_address: str,
        high_watermark: int = 1,
        sleep_timeout: int = 10,
    ):
        self.pull_connect_address = pull_connect_address
        self.should_run = True
        self.sleep_timeout = sleep_timeout
        self.poller = zmq.Poller()
        self.queue = context.socket(zmq.PULL)
        self.queue.set_hwm(high_watermark)
        self.poller.register(self.queue, zmq.POLLIN)

    def handle_exception(self, e):
        logger.exception(f"{self.__class__.__name__} interrupted by error")

    def connect(self):
        logger.info(f"Connecting to pull address: {self.pull_connect_address}")
        self.queue.connect(self.pull_connect_address)

    def run(self):
        self.connect()
        logger.info(f"Starting {self.__class__.__name__}")
        while self.should_run:
            try:
                self.loop_once()
            except Exception as e:
                self.handle_exception(e)
                break

    def loop_once(self):
        self.process_queue()

    def pull_queue(self):
        logger.info(f"Waiting for job")
        socks = dict(self.poller.poll())
        if self.queue in socks and socks[self.queue] == zmq.POLLIN:
            return self.queue.recv_json()

    def process_queue(self):
        info = self.pull_queue()
        logger.info(f"received payload {info}")
        return

    def process_job(self, info: dict):
        url = info.get("url")
        repo = info.get("repo")
        owner = info.get("owner")
        build_id = info.get("build_id")
        access_token = info.get("access_token")

        missing_fields = []

        if not url:
            missing_fields.append("url")

        if not repo:
            missing_fields.append("repo")

        if not repo:
            missing_fields.append("owner")

        if missing_fields:
            logger.error(f"missing fields: {missing_fields} in {info}")
            return

        api = DroneAPIClient(
            url=url,
            access_token=access_token,
        )
        # gevent.sleep()
        self.fetch_data(api, repo, owner)
        # gevent.sleep(self.sleep_timeout)

    def fetch_data(self, api: DroneAPIClient, repo: str, owner: str, build_id: int):
        build = api.get_build_info(repo, owner, build_id)
        failed_stages = build.failed_stages()
        for stage in failed_stages:
            self.publish(
                "build:failed",
            )
        # 1. Poll zmq for job with build_id
        # 2. Iterate over failed stages
        # 3. For each failed stage check whether a failure notification was already sent
        #      otherwise publish zmq event "stage failed" which will store this information in the db to prevent emitting the event twice
        # 4. Iterate over pending stages (finished_at == None)
        # 5. For each pending stage schedule a new job to monitor build_id
        # 6. If the build has all its stages completed with success in all steps
        #      then publish zmq event "build succeeded" which will store this information to the db to prevent emitting the event twice
        pass
