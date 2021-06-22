FROM gabrielfalcao/drone-ci-butler-base

VOLUME /drone-ci-butler

ENV VENV /venv/
ENV PATH "/venv/bin:${PATH}"
ENV PYTHONPATH /app/
ENV UPLOAD_FOLDER /butler/file-uploads
ENV PIP_CACHE_DIR /pip/cache
ENV DRONE_CI_BUTLER_CONFIG_PATH /butler/drone-ci-butler.yml

# RUN sysctl net.ipv4.conf.all.forwarding=1
# RUN iptables -P FORWARD ACCEPT
RUN mkdir -p /logs

COPY . /app/
RUN /venv/bin/pip install -e /app > /logs/pip.log


ENV DRONE_CI_BUTLER_WEB_HOSTNAME 0.0.0.0
ENV DRONE_CI_BUTLER_WEB_PORT 4000
ENV DRONE_GITHUB_CLIENT_ID 0
ENV DRONE_GITHUB_CLIENT_SECRET 0
ENV DRONE_SLACK_CLIENT_ID 0
ENV DRONE_SLACK_CLIENT_SECRET 0
ENV DRONE_GITHUB_OWNER drone-ci-monitor
ENV DRONE_GITHUB_REPO drone-api-test
ENV DRONE_SERVER_URL "https://drone-ci-server.ngrok.io"
ENV SECRET_KEY insecure
ENV SESSION_FILE_DIR /tmp/flask-session

RUN drone-ci-butler check

EXPOSE 4000
EXPOSE 5001
EXPOSE 5002
EXPOSE 5555
EXPOSE 5556
EXPOSE 6666
EXPOSE 7777

CMD drone-ci-butler web
