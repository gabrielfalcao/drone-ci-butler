FROM gabrielfalcao/drone-ci-butler-base

VOLUME /drone-ci-butler

ENV VENV /venv/
ENV PATH "/venv/bin:${PATH}"
ENV PYTHONPATH /app/
ENV UPLOAD_FOLDER /notequalia.io/file-uploads
ENV PIP_CACHE_DIR /pip/cache

COPY . /app/
RUN /venv/bin/pip install /app

RUN make tests

RUN drone-ci-butler check
ENV DRONE_CI_BUTLER_PORT 5000
ENV DRONE_CI_BUTLER_VERSION 4

EXPOSE 5000
EXPOSE 4242
EXPOSE 6969

CMD drone-ci-butler web --port=$DRONE_CI_BUTLER_PORT
