# syntax=docker/dockerfile:1.4
FROM --platform=$BUILDPLATFORM python:3.11-alpine AS builder

WORKDIR /app

COPY requirements.txt /app
RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install -r requirements.txt

COPY . /app

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]
