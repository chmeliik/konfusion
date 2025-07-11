FROM registry.access.redhat.com/ubi9/python-312:latest@sha256:81ecc946acac7523ab3c7fe10ca4cf7db29bb462c2ab5c6c57c7b57d39f38b19 AS build-python

WORKDIR /app/konfusion

COPY --chown=default requirements.txt requirements.txt
RUN python3 -m venv venv && \
    venv/bin/pip install -r requirements.txt

COPY --chown=default . .
RUN venv/bin/pip install . && \
    venv/bin/pip install ./packages/konfusion-build-commands


FROM registry.access.redhat.com/ubi9/python-312:latest@sha256:81ecc946acac7523ab3c7fe10ca4cf7db29bb462c2ab5c6c57c7b57d39f38b19

USER root
RUN dnf -y install skopeo
USER default

WORKDIR /app/konfusion
COPY --from=build-python /app/konfusion/venv /app/konfusion/venv

ENTRYPOINT ["/app/konfusion/venv/bin/konfusion"]
