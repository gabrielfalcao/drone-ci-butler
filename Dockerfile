FROM gabrielfalcao/drone-ci-butler-base

VOLUME /notequalia.io

ENV VENV /venv/
ENV PATH "/venv/bin:${PATH}"
ENV PYTHONPATH /app/
ENV UPLOAD_FOLDER /notequalia.io/file-uploads
ENV PIP_CACHE_DIR /pip/cache

COPY . /app/
RUN /venv/bin/pip install /app

RUN make tests

RUN cookmylist-scraper check
ENV SCRAPER_ENGINE_PORT 5000
ENV SCRAPER_ENGINE_VERSION 4

EXPOSE 5000
EXPOSE 4242
EXPOSE 6969


CMD scraper-engine web "--port=$SCRAPER_ENGINE_PORT"
