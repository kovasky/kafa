#Copyright 2021 by Kovasky Buezo and Fernando Saenz
#This file is part of the Thermostat Enhancer presented for MakeUofT 
#Written by Kovasky Buezo <kab310@mun.ca>, February 2021

FROM arm32v6/python:3.8-alpine3.12

LABEL maintainer="Kovasky Buezo"

COPY requirements.txt /
COPY app.py /
COPY entrypoint.sh /

RUN set -ex && apk --no-cache add sudo alpine-sdk

#taken from https://github.com/zinen/docker-alpine-pigpiod
RUN wget --output-document=download.zip https://github.com/joan2937/pigpio/archive/master.zip \
    && mkdir download \
    && unzip -d download download.zip \
    && cd /download/* \
    && sed -i -e 's/ldconfig/echo ldconfig disabled/g' Makefile \
    && make \
    && make install

RUN pip3 install -r /requirements.txt
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

EXPOSE 5000

ENTRYPOINT ["sh", "/entrypoint.sh"]