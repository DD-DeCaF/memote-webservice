FROM python:3.6-slim

ENV PYTHONUNBUFFERED=1
# The sympy cache causes significant memory leaks as it is currently used by
# optlang. Disable it by default.
ENV SYMPY_USE_CACHE=no

ENV APP_USER=kaa
ENV HOME="/home/${APP_USER}"

ARG UID=1000
ARG GID=1000

ARG CWD="${HOME}/app"

ENV PYTHONPATH="${CWD}/src"

RUN groupadd --system --gid "${GID}" "${APP_USER}" \
    && useradd --system --create-home --home-dir "${HOME}" \
        --uid "${UID}" --gid "${APP_USER}" "${APP_USER}"

WORKDIR "${CWD}"

COPY requirements.txt "${CWD}/"

# `g++` is required for building `gevent` but all build dependencies are
# later removed again.
RUN set -eux \
    && apt-get update \
    && apt-get install --yes --only-upgrade openssl ca-certificates \
    && apt-get install --yes --no-install-recommends \
        build-essential libssl-dev \
    && pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt \
    && rm -rf /root/.cache/pip \
    && apt-get purge --yes build-essential \
    && apt-get autoremove --yes \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY . "${CWD}/"

RUN chown -R "${APP_USER}:${APP_USER}" "${CWD}"
