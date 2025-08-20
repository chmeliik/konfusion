FROM registry.access.redhat.com/ubi9/python-312:latest@sha256:81ecc946acac7523ab3c7fe10ca4cf7db29bb462c2ab5c6c57c7b57d39f38b19 AS build-python

WORKDIR /app/konfusion

COPY --chown=default requirements.txt requirements.txt
RUN python3 -m venv venv && \
    venv/bin/pip install -r requirements.txt

COPY --chown=default . .
RUN venv/bin/pip install --no-deps . && \
    venv/bin/pip install --no-deps ./packages/konfusion-build-commands


FROM registry.access.redhat.com/ubi9/python-312:latest@sha256:81ecc946acac7523ab3c7fe10ca4cf7db29bb462c2ab5c6c57c7b57d39f38b19

USER root

RUN dnf -y install skopeo

WORKDIR /app/konfusion
COPY --from=build-python /app/konfusion/venv /app/konfusion/venv

RUN ln -s /app/konfusion/venv/bin/konfusion /usr/local/bin/konfusion

ENV HOME=/home/default
RUN usermod --move-home --home "$HOME" default

USER default
