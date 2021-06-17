import time
import logging
import gevent
import zmq.green as zmq
from collections import defaultdict

from drone_ci_butler.logs import get_logger
from drone_ci_butler.drone_api import DroneAPIClient

from .base import context


# QueueServer is inspired by
# https://zguide.zeromq.org/docs/chapter5/#High-Speed-Subscribers-Black-Box-Pattern
# except that it uses a REP socket instead of a subscriber socket,
# this way it can block clients from enqueueing more jobs that can be
# processed.


class QueueClient(object):
    def __init__(
        self,
        rep_connect_address: str,
        rep_high_watermark: int = 1,
    ):
        self.logger = get_logger("queue-client")
        self.rep_connect_address = rep_connect_address
        self.socket = context.socket(zmq.REQ)
        self.socket.set_hwm(rep_high_watermark)
        self.__connected__ = False

    def connect(self):
        self.logger.debug(f"connecting to {self.rep_connect_address}")
        self.socket.connect(self.rep_connect_address)
        self.__connected__ = True

    def close(self):
        self.__connected__ = False
        self.socket.disconnect(self.rep_connect_address)

    def send(self, job: dict):
        if not self.__connected__:
            raise RuntimeError(f"{self} is not connected")

        self.socket.send_json(job)
        response = self.socket.recv_json()
        self.logger.debug(f"{response}")
        return response

    def __del__(self):
        if getattr(self, "__connected__", False):
            try:
                self.close()
            except Exception as e:
                self.logger.warning("error to disconnect socket")


class QueueServer(object):
    def __init__(
        self,
        rep_bind_address: str,
        push_bind_address: str,
        rep_high_watermark: int = 1,
        push_high_watermark: int = 1,
        sleep_timeout: float = 0.1,
        log_level: int = logging.WARNING,
        postmortem_sleep_seconds: int = 10,
    ):
        self.logger = get_logger("queue-server")
        self.log_level = log_level
        self.rep_bind_address = rep_bind_address
        self.push_bind_address = push_bind_address
        self.should_run = True
        self.sleep_timeout = sleep_timeout
        self.poller = zmq.Poller()
        self.push = context.socket(zmq.PUSH)
        self.rep = context.socket(zmq.REP)
        self.poller.register(self.push, zmq.POLLOUT)
        self.poller.register(self.rep, zmq.POLLIN | zmq.POLLOUT)

        self.rep.set_hwm(rep_high_watermark)
        self.push.set_hwm(push_high_watermark)

    def handle_exception(self, e):
        self.disconnect()
        self.logger.exception(f"{self.__class__.__name__} interrupted by error")
        self.logger.info(
            "restoring health of worker in {self.postmortem_sleep_seconds} seconds"
        )
        gevent.sleep(self.postmortem_sleep_seconds)
        self.listen()

    def listen(self):
        self.logger.info(f"Listening on REP address: {self.rep_bind_address}")
        self.rep.bind(self.rep_bind_address)
        self.logger.info(f"Listening on PUSH address: {self.push_bind_address}")
        self.push.bind(self.push_bind_address)
        self.logger.setLevel(self.log_level)

    def disconnect(self):
        self.rep.disconnect(self.rep_bind_address)
        self.logger.info(
            f"Releasing connections from REP address: {self.rep_bind_address}"
        )
        self.push.disconnect(self.push_bind_address)
        self.logger.info(
            f"Releasing connections from PUSH address: {self.push_bind_address}"
        )

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
        self.disconnect()

    def loop_once(self):
        self.process_queue()

    def push_job(self, data: dict):
        self.logger.info(f"Waiting for socket to become available to push job")
        socks = dict(self.poller.poll())
        if self.push in socks and socks[self.push] == zmq.POLLOUT:
            self.push.send_json(data)
            return True

    def handle_request(self):
        socks = dict(self.poller.poll())
        if self.rep in socks and socks[self.rep] == zmq.POLLIN:
            data = self.rep.recv_json()
            if data:
                self.logger.info(f"processing job {data}")
                while not self.push_job(data):
                    gevent.sleep(self.sleep_timeout)
                self.rep.send_json(data)
                return data

    def process_queue(self):
        data = self.handle_request()
        if not data:
            gevent.sleep()
            return
