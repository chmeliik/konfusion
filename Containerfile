FROM registry.access.redhat.com/ubi9/python-312:latest@sha256:a3af61fdae215cd8d8f67f8f737064b353dc0592567099de48b3c2563314810d AS build-python

WORKDIR /app/konfusion

COPY --chown=default requirements.txt requirements.txt
RUN python3 -m venv venv && \
    venv/bin/pip install -r requirements.txt

COPY --chown=default . .
RUN venv/bin/pip install --no-deps . && \
    venv/bin/pip install --no-deps ./packages/konfusion-build-commands


FROM registry.access.redhat.com/ubi9/python-312:latest@sha256:a3af61fdae215cd8d8f67f8f737064b353dc0592567099de48b3c2563314810d

USER root

RUN dnf -y install skopeo

WORKDIR /app/konfusion
COPY --from=build-python /app/konfusion/venv /app/konfusion/venv

RUN ln -s /app/konfusion/venv/bin/konfusion /usr/local/bin/konfusion

ENV HOME=/home/default
RUN usermod --move-home --home "$HOME" default

USER default
