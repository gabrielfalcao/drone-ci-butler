import zmq.green as zmq
from collections import defaultdict
from drone_ci_butler.logs import logger
from drone_ci_butler.drone_api import DroneAPIClient

context = zmq.Context()


class BaseWorker(object):
    def __init__(self, **options):
        self.options = options
        self.should_run = True
        self.sockets = SocketManager(zmq, context, serialization_backend=JSON())
        self.sockets.get_or_create("queue", zmq.PULL, zmq.POLLIN)
        self.sockets.get_or_create("pub", zmq.PUB, zmq.POLLOUT)
        self.sockets.set_socket_option("queue", zmq.HWM, 1)
        self.initialize()

    def initialize(self):
        self.sleep_timeout = self.options.get("sleep_timeout")

    def handle_exception(self, e):
        logger.exception(f"{self.__class__.__name__} interrupted by error")

    def publish(self, topic: str, data: dict):
        self.sockets.publish_safe(
            "pub",
            topic,
            data,
        )

    def connect_and_bind(self):
        pull_address = self.options["pull_address"]
        pub_address = self.options["pub_address"]
        self.sockets.connect("queue", pull_address)
        self.sockets.connect("pub", pub_address)

    def run(self):
        self.connect_and_bind()
        while self.should_run:
            try:
                self.loop_once()
            except KeyboardInterrupt:
                return 0
            except Exception as e:
                self.handle_exception(e)
                return 1

    def loop_once(self):
        raise NotImplementedError

    def loop_once(self):
        info = self.sockets.recv_safe(
            "queue",
            timeout=self.sleep_timeout,
            polling_timeout=self.sleep_timeout * 1000,
        )
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
        gevent.sleep()
        self.fetch_data(api, repo, owner)
        gevent.sleep(self.sleep_timeout)

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
