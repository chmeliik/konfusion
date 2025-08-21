FROM registry.access.redhat.com/ubi9/python-312:latest@sha256:83b01cf47b22e6ce98a0a4802772fb3d4b7e32280e3a1b7ffcd785e01956e1cb AS build-python

WORKDIR /app/konfusion

COPY --chown=default requirements.txt requirements.txt
RUN python3 -m venv venv && \
    venv/bin/pip install -r requirements.txt

COPY --chown=default . .
RUN venv/bin/pip install --no-deps . && \
    venv/bin/pip install --no-deps ./packages/konfusion-build-commands


FROM registry.access.redhat.com/ubi9/python-312:latest@sha256:83b01cf47b22e6ce98a0a4802772fb3d4b7e32280e3a1b7ffcd785e01956e1cb

USER root

RUN dnf -y install skopeo

WORKDIR /app/konfusion
COPY --from=build-python /app/konfusion/venv /app/konfusion/venv

RUN ln -s /app/konfusion/venv/bin/konfusion /usr/local/bin/konfusion

ENV HOME=/home/default
RUN usermod --move-home --home "$HOME" default

USER default
