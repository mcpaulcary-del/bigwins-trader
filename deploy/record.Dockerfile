# Record image (BF-D93): the environment the paper record was built and registered on,
# exactly. The research jobs run in it UNEDITED, with the record tree mounted at the
# cloud's own absolute path (deploy/record.sh). It is not the trader image and never runs
# trading code; it has no Docker socket and one optional secret (the EODHD token file).
#
#   Ubuntu 24.04      -> pdftotext (poppler) 24.02.0, the cloud's: NEWS-C batches are
#                        built from its text output and must be byte-identical
#   Python 3.13.18    -> copied from the official image (the host and the trader are 3.12)
#   libraries         -> deploy/record_requirements.txt: the cloud's pip freeze, every wheel
#                        pinned by SHA-256, no dependency resolution, binary wheels only
#
# The build fails if Python or poppler is another version; the runner checks the library
# versions again before every job (record/ENVIRONMENT.json). TODO before the first build on
# the server (it could not be done from the research environment, which cannot reach a
# container registry): replace the two tags below by digests (docker buildx imagetools
# inspect <tag>), as deploy/Dockerfile does.
ARG PY_IMAGE=python:3.13.18-slim-bookworm
ARG BASE_IMAGE=ubuntu:24.04
FROM ${PY_IMAGE} AS py
FROM ${BASE_IMAGE}
ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1 TZ=UTC PATH="/usr/local/bin:$PATH"
RUN apt-get update && apt-get install -y --no-install-recommends \
      poppler-utils ca-certificates tzdata libssl3t64 libffi8 libsqlite3-0 zlib1g libbz2-1.0 \
      liblzma5 libreadline8t64 libuuid1 libexpat1 libgomp1 \
    && rm -rf /var/lib/apt/lists/*
COPY --from=py /usr/local /usr/local
RUN ldconfig \
    && python3 -c "import sys, ssl, sqlite3, ctypes, lzma, bz2, zoneinfo; assert sys.version_info[:3] == (3, 13, 18), sys.version" \
    && pdftotext -v 2>&1 | grep -q 'version 24.02.0'
COPY deploy/record_requirements.txt /tmp/record_requirements.txt
RUN python3 -m pip install --no-cache-dir --require-hashes --no-deps --only-binary :all: \
      -r /tmp/record_requirements.txt \
    && rm /tmp/record_requirements.txt \
    && python3 -c "import pandas, numpy, scipy, requests, exchange_calendars, sklearn, lightgbm, duckdb"
RUN useradd --uid 10002 --no-create-home --shell /usr/sbin/nologin bwrecord
USER 10002:10002
WORKDIR /tmp
