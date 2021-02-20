#Copyright 2021 by Kovasky Buezo and Fernando Saenz
#This file is part of the Thermostat Enhancer presented for MakeUofT
#Written by Kovasky Buezo <kab310@mun.ca>, February 2021

FROM python:latest
LABEL maintainer="Kovasky Buezo"

COPY requirements.txt /webapp/
RUN pip3 install -r /webapp/requirements.txt

COPY app.py /webapp/
ADD static /webapp/static/
ADD templates /webapp/templates/

COPY entrypoint.sh /

EXPOSE 5001

ENTRYPOINT ["sh", "/entrypoint.sh"]
