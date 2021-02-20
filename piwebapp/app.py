""" 
Copyright 2021 by Kovasky Buezo and Fernando Saenz
This file is part of the Thermostat Enhancer presented for MakeUofT 
Written by Kovasky Buezo <kab310@mun.ca>, February 2021
"""

import time
import board
import busio
import dht11
import mysql.connector
import pigpio
import os.path
import logging
import adafruit_ads1x15.ads1115 as ADS
from gpiozero import LED
from adafruit_ads1x15.analog_in import AnalogIn
from flask import Flask, jsonify
from multiprocessing import Process, Value, Array
from flask_cors import CORS
from datetime import datetime
from numpy import interp 

pinSERVO = 18
pinRED = 26
pinBLUE = 13
pinGREEN = 19
pinDHT = 27

connection = mysql.connector.connect(
        host="192.168.2.67",
        port=32773,
        user="root",
        password="root",
        database="thermostat"
        )

insertAnalytics = """
INSERT INTO analytics
(date,ambientTemperature,desiredTemperature)
VALUES ( %s, %s ,%s)
"""

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
dht = dht11.DHT11(pin=pinDHT)
pwm = pigpio.pi()
pwm.set_mode(pinSERVO,pigpio.OUTPUT)
pwm.set_PWM_frequency(pinSERVO, 50)
ledGREEN = LED(pinGREEN)
ledRED = LED(pinRED)
ledBLUE = LED(pinBLUE)

#0 = variableResistorOld, 1 = variableResistorNew, 2 = oldWebTemp, 3 = newWebTemp
#4 = maxServoAngle, 5 = ambientTemp, 6 = currentDesiredTemp
#7 = h1, 8 = h2, 9 = flag
sensorData = Array("d", range(10)) 
for i in range(10):
    sensorData[i] = 0


def deviceCheck(loop_on,sensorData):
    global ads
    chan = AnalogIn(ads,ADS.P0)
    while True:
        if abs(sensorData[1] - chan.value) > 64:
            sensorData[1] = chan.value
        time.sleep(0.1)

def startup(sensorData):
    global ads
    global pinSERVO
    global ledRED
    ledRED.on()
    pwm.set_servo_pulsewidth(pinSERVO,500) #set to 0
    chan = AnalogIn(ads,ADS.P1)
    maxVal = 0
    time.sleep(1.5)
    for i in range(0,181,5):
        par = interp(i,[0,180],[500,2500])
        pwm.set_servo_pulsewidth(pinSERVO, par)
        time.sleep(1)
        currentVal = chan.value
        if maxVal < currentVal:
            maxVal = currentVal
        elif i > 10:
            break
    pwm.set_PWM_dutycycle(pinSERVO,0) #turn of
    sensorData[4] = interp(maxVal,[0,16000],[0,180]) - 2
    ledRED.off()

def isTimeBetween(start, end, now=None):
    now = now or datetime.now()
    if start < end:
        return now >= start and now <= end
    else: 
        return now >= start or now <= end

def updateServo(loop_on,sensorData):
    global pwm
    global pinSERVO
    global ledRED
    while loop_on.value:
        if sensorData[1] != sensorData[0]:
            ledRED.on()
            val = interp(sensorData[1],[0,26672],[500,2500])
            sensorData[0] = sensorData[1]
            pwm.set_servo_pulsewidth(pinSERVO,val)
            sensorData[6] = interp(val,[500,2500],[0,30])
            if val < 550 or val > 2450: 
                time.sleep(0.9)
                pwm.set_servo_pulsewidth(pinSERVO,0)
        elif sensorData[2] != sensorData[3]:
            ledRED.on()
            sensorData[2] = sensorData[3]
            val = interp(sensorData[3],[0,30],[500,2500])
            pwm.set_servo_pulsewidth(pinSERVO,val)
            sensorData[6] = sensorData[3]
            if val < 550 or val > 2450:
                time.sleep(0.9)
                pwm.set_servo_pulsewidth(pinSERVO,0)
        else:
            now = datetime.now()
            start = datetime.now().replace(hour=int(sensorData[7]),minute=0,second=0,microsecond=0)
            end = datetime.now().replace(hour = int(sensorData[8]),minute=0,second=0,microsecond=0)
            if not(isTimeBetween(start,end,now)):
                pwm.set_servo_pulsewidth(pinSERVO,1334)
                sensorData[6] = 8
                sensorData[9] = 1
            elif sensorData[9]:
                pwm.set_servo_pulsewidth(pinSERVO,1833)
                sensorData[6] = 20
                sensorData[9] = 0
        ledRED.off()
        time.sleep(0.1)

def sendAnalytics(loop_on,sensorData):
    global connection
    global insertAnalytics
    global dht
    global ledBLUE
    while loop_on.value:
        ledBLUE.on()
        cursor = connection.cursor()
        res = dht.read()
        while not res.is_valid():
            res = dht.read()
        sensorData[5] = res.temperature
        cursor.executemany(insertAnalytics, [(datetime.now(),sensorData[5],sensorData[6]),])
        connection.commit()
        cursor.close()
        ledBLUE.off()
        time.sleep(300) #we are sending analytics evry 5 mins

app = Flask(__name__)
CORS(app)

@app.route('/')
@app.route('/home')
@app.route('/index')
def index():
    return str("Server on Pi")

@app.route('/status/<device>')
def status(device):
    global sensorData
    global ledBLUE
    global pwm
    global pinSERVO
    ledBLUE.on()
    if device == "currentTemp":
        return jsonify(ambientTemp=sensorData[5],desiredTemp=sensorData[6],off=ledBLUE.off())
    if device == "hour":
        return jsonify(start=sensorData[7],end=sensorData[8],off=ledBLUE.off())

@app.route('/set/<device>/<value1>/<value2>')
def setDevice(device,value1,value2):
    global sensorData
    global ledBLUE
    ledBLUE.on()
    if device == "desiredTemp":
        sensorData[3] = float(value1)
        return jsonify(desiredTemp=sensorData[3],off=ledBLUE.off())
    elif device == "hour":
        sensorData[7] = float(value1)
        sensorData[8] = float(value2)
        return jsonify(hour1=str(value1) + ":00",hour2=str(value2)+":00",off=ledBLUE.off())

@app.route('/logs')
def getLogs():
    if os.path.exists("pi.log"):
        f = open("pi.log")
        response = app.response_class(response=f.read(),status=200,mimetype='text/plain')
        response.headers["Content-Type"] = "text/plain; charset=utf-8"
        return response
    else:
        return "No Logs available"

if __name__ == "__main__":
    startup(sensorData)
    ledGREEN.on()
    enableProcess = Value('b', True)
    deviceCheckProcess = Process(target=deviceCheck, args=(enableProcess,sensorData,))
    sendAnalyticsProcess = Process(target=sendAnalytics,args=(enableProcess,sensorData,))
    updateServoProcess = Process(target=updateServo,args=(enableProcess,sensorData,))
    deviceCheckProcess.start()
    sendAnalyticsProcess.start()  
    updateServoProcess.start()
    logging.basicConfig(filename='pi.log',level=logging.DEBUG)
    app.run(debug=True, port=5000, host='0.0.0.0', use_reloader=False)
    deviceCheckProcess.join()
    sendAnalyticsProcess.join()
    updateServoProcess.join()
    connection.close()
    ledGREEN.off()