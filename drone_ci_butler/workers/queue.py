import time
import gevent
from gevent.pool import Pool
import zmq.green as zmq
from collections import defaultdict

from drone_ci_butler.logs import get_logger
from drone_ci_butler.drone_api import DroneAPIClient

from .base import context



class QueueClient(object):
    def __init__(
        self,
        rep_connect_address: str,
        rep_high_watermark: int = 10,
    ):
        self.logger = get_logger('drone_ci_butler.QueueClient')
        self.rep_connect_address = rep_connect_address
        self.socket = context.socket(zmq.REQ)
        self.socket.set_hwm(rep_high_watermark)
        self.__connected__ = False

    def connect(self):
        self.logger.info(f'connecting to {self.rep_connect_address}')
        self.socket.connect(self.rep_connect_address)
        self.__connected__ = True

    def send(self, job: dict):
        if not self.__connected__:
            raise RuntimeError(f'{self} is not connected')

        self.logger.info(f'sending job')
        self.socket.send_json(job)
        self.logger.info(f'waiting for response')
        response = self.socket.recv_json()
        self.logger.info(f'sent receipt {response}')


class QueueServer(object):
    def __init__(
        self,
        rep_bind_address: str,
        push_bind_address: str,
        rep_high_watermark: int = 10,
        sleep_timeout: float = 0.1,
    ):
        self.logger = get_logger('queue-server')
        self.rep_bind_address = rep_bind_address
        self.push_bind_address = push_bind_address
        self.should_run = True
        self.sleep_timeout = sleep_timeout
        self.poller = zmq.Poller()
        self.push = context.socket(zmq.PUSH)
        self.rep = context.socket(zmq.REP)
        self.poller.register(self.push, zmq.POLLOUT)
        self.poller.register(self.rep, zmq.POLLIN | zmq.POLLOUT)

        # self.rep.set_hwm(rep_high_watermark)
        self.pool = Pool(1)

    def handle_exception(self, e):
        self.logger.exception(f"{self.__class__.__name__} interrupted by error")

    def listen(self):
        self.logger.info(f"Listening on REP address: {self.rep_bind_address}")
        self.rep.bind(self.rep_bind_address)
        self.logger.info(f"Listening on PUSH address: {self.push_bind_address}")
        self.push.bind(self.push_bind_address)

    def run(self):
        self.listen()
        self.logger.info(f"Starting {self.__class__.__name__}")
        while self.should_run:
            try:
                self.loop_once()
                gevent.sleep()
            except Exception as e:
                self.handle_exception(e)
                break
    def loop_once(self):
        self.process_queue()

    def push_job(self, data: dict):
        self.logger.info(f"Waiting for socket to become available to push job")
        socks = dict(self.poller.poll())
        if self.push in socks and socks[self.push] == zmq.POLLOUT:
            return self.push.send_json(data)

    def handle_request(self):
        socks = dict(self.poller.poll())
        if self.rep in socks and socks[self.rep] == zmq.POLLIN:
            data = self.rep.recv_json()
            if data:
                self.logger.info(f"processing request")
                self.rep.send_json({
                    "reply": time.time(), "data": data
                })
                return data


    def process_queue(self):
        data = self.handle_request()
        if not data:
            gevent.sleep()
            return
        self.logger.info(f"processing job {data}")
        self.push_job(data)

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
            self.logger.error(f"missing fields: {missing_fields} in {info}")
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
