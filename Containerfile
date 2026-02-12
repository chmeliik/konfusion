FROM registry.access.redhat.com/ubi9/python-312:latest@sha256:3da39d0c938994161bdf9b6b13eb2eacd9a023c86dd5166f3da31df171c88780 AS build-python

WORKDIR /app/konfusion

COPY --chown=default requirements.txt requirements.txt
RUN python3 -m venv venv && \
    venv/bin/pip install -r requirements.txt

COPY --chown=default . .
RUN venv/bin/pip install --no-deps . && \
    venv/bin/pip install --no-deps ./packages/konfusion-build-commands


FROM registry.access.redhat.com/ubi9/python-312:latest@sha256:3da39d0c938994161bdf9b6b13eb2eacd9a023c86dd5166f3da31df171c88780

USER root

RUN dnf -y install skopeo

WORKDIR /app/konfusion
COPY --from=build-python /app/konfusion/venv /app/konfusion/venv

RUN ln -s /app/konfusion/venv/bin/konfusion /usr/local/bin/konfusion

ENV HOME=/home/default
RUN usermod --move-home --home "$HOME" default

USER default
