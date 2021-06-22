import gevent
import zmq.green as zmq
from collections import defaultdict
from drone_ci_butler.config import Config, config
from drone_ci_butler.logs import get_logger
from drone_ci_butler.drone_api import DroneAPIClient
from drone_ci_butler.networking import resolve_zmq_address

from .base import context


class PullerWorker(object):
    __log_name__ = "puller-worker"

    worker_id: int = None

    def __init__(
        self,
        pull_connect_address: str,
        worker_id: str,
        config: Config = config,
        high_watermark: int = 1,
        postmortem_sleep_seconds: int = 10,
    ):
        self.worker_id = worker_id
        self.logger = get_logger(f"{self.__log_name__}:{worker_id}")

        self.config = config
        self.postmortem_sleep_seconds = postmortem_sleep_seconds
        self.pull_connect_address = resolve_zmq_address(pull_connect_address)
        self.should_run = True
        self.poller = zmq.Poller()
        self.queue = context.socket(zmq.PULL)
        self.queue.set_hwm(high_watermark)
        self.github_owner = config.drone_api_owner
        self.github_repo = config.drone_api_repo
        self.poller.register(self.queue, zmq.POLLIN)
        self.api = DroneAPIClient.from_config(config)

    @property
    def name(self) -> str:
        worker_id = getattr(self, "worker_id", None)
        return f"{self.__class__.__name__}:{worker_id}"

    def handle_exception(self, e):
        self.logger.exception(f"{self.name} interrupted by error")

    def connect(self):
        self.logger.info(f"Connecting to pull address: {self.pull_connect_address}")
        self.queue.connect(self.pull_connect_address)

    def run(self):
        self.connect()
        self.logger.info(f"{self.name} is Online and ready for jobs")
        while self.should_run:
            try:
                self.loop_once()
            except Exception as e:
                self.handle_exception(e)
                break

    def loop_once(self):
        try:
            self.process_queue()
        except Exception as e:
            self.logger.exception(f"failed to process queue")
            self.logger.info(
                "restoring health of worker in {self.postmortem_sleep_seconds} seconds"
            )

            gevent.sleep(self.postmortem_sleep_seconds)

    def pull_queue(self):
        self.logger.debug(f"Waiting for job")
        socks = dict(self.poller.poll())
        if self.queue in socks and socks[self.queue] == zmq.POLLIN:
            return self.queue.recv_json()

    def process_queue(self):
        info = self.pull_queue()
        self.logger.debug(f"processing job")
        self.process_job(info)
