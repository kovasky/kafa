#!/bin/bash

#Copyright 2021 by Kovasky Buezo and Fernando Saenz
#This file is part of the Thermostat Enhancer presented for MakeUofT 
#Written by Kovasky Buezo <kab310@mun.ca>, February 2021

sudo pigpiod
python3 /app.py > pi.log