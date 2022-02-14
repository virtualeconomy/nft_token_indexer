FROM python:3.9-slim

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y git gcc

COPY requirements.txt /

RUN pip3 install --no-cache-dir -r /requirements.txt

COPY app/ /app
WORKDIR /app

ENV APP_ENV docker
