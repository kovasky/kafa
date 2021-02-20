""" 
Copyright 2021 by Kovasky Buezo and Fernando Saenz
This file is part of the Thermostat Enhancer presented for MakeUofT
Written by Kovasky Buezo <kab310@mun.ca>, February 2021
"""

import requests
import time
from flask import Flask, jsonify, render_template
from multiprocessing import Process, Value
from flask_cors import CORS
import mysql.connector 
import pandas as pd

app = Flask(__name__,static_url_path='/static')

connection = mysql.connector.connect(
  host="192.168.2.67",
  port=32773,
  user="root",
  password="root",
  database="thermostat"
)

cursor = connection.cursor()
selectAnalytics = "SELECT * FROM analytics LIMIT 288"

@app.route('/')
@app.route('/home')
@app.route('/index')
def index():
    req = requests.get('http://192.168.2.71:5000/status/currentTemp')
    data = req.json()
    return render_template('index.html',ambientTemp=float(data['ambientTemp']),desiredTemp=float(data['desiredTemp']))

@app.route('/logs')
def logs():
    req = requests.get('http://192.168.2.71:5000/logs')
    return render_template('logs.html',logs=req.content.decode("utf-8"))

@app.route('/settings')
def settings():
    req = requests.get('http://192.168.2.71:5000/status/hour')
    data = req.json()
    return render_template('settings.html',start=int(data['start']),end=int(data['end']))
   
@app.route('/stats')
def stats():
    global connection
    global cursor
    global selectAnalytics
    cursor.execute(selectAnalytics)
    data = cursor.fetchall()
    df = pd.DataFrame( [[ij for ij in i] for i in data] )
    df.rename(columns={0: 'Date', 1: 'AmbientTemperature', 2: 'DesiredTemperature'}, inplace=True)
    return render_template("stats.html",set1="Ambient",set2="Desired",labels=df['Date'],ambient=df['AmbientTemperature'],desired=df['DesiredTemperature'])

if __name__ == "__main__":
   app.run(debug=True, port=5001, host='0.0.0.0', use_reloader=False)