"""
N2YO.com API to MQTT publishing service for Satlight Installation.
Tamás Nyilánszky (c) 2020
Heavy Detail
"""

import json
import time
import paho.mqtt.client as mqtt
import requests


class Satellite:
    def __init__(self, timestamp, satid, TLE):
        self.timestamp = timestamp
        self.satid = satid
        self.TLE = TLE

    def __eq__(self, other):
        if self.satid == other.satid:
            return True
        else:
            return False


satList = []


"""
SETUP VARIABLES
"""
#MQTT
mqttc = mqtt.Client()
mqttc.username_pw_set('satlight','aboveus')
MQTT_TOPIC = "satlight/sat"

#API
API_FETCH_TIMEOUT = 15
SATBUFFER_TIMEOUT = 120
WATCH_DEGREE = 5
API_KEY = 'R5H4CQ-TJQTXV-BQ53MB-48ZP'

def main():
    print("Satlight N2Y0.com API to MQTT Publisher.\nDeveloped by Tamás Nyilánszky / @heavydetail (c) 2020\n...")

    #setup mqtt
    mqttc.connect("localhost",1883, 60)
    mqttc.subscribe(MQTT_TOPIC, 0)
    mqttc.loop_start()

    while True: #MAIN LOOP
        
        #fetch API data
        r = requests.get(url='http://www.n2yo.com/rest/v1/satellite/above/48.20849/16.37208/500/'+str(WATCH_DEGREE)+'/0&apiKey='+API_KEY)
       #print(r.json())

        data = json.loads(r.text)
        #print('Satcount: ')
        satcount = data['info']['satcount']

        print("Fresh API Data fetched.\nSatcount:"+str(data['info']['satcount']))
        #print(data['info']['satcount'])
        #print('\n')

        #print(r.json())
        #print(data)
        
        print('\nTransactions: ')
        print(data['info']['transactionscount'])

        if data['info']['transactionscount'] > 980:
            time.sleep(600) # wait for transactions to reduce.

        for i in range(satcount):
            #fetch additional satellite data for each, TLE
            r2 = requests.get(url='https://www.n2yo.com/rest/v1/satellite/tle/'+str(data['above'][i]['satid'])+'&apiKey='+API_KEY)
            satdata = json.loads(r2.text)
            #print(satdata)
            print("######### SATDATA ##########")
            print(satdata['info']['satname'])
            print("TLE:  \n" + satdata['tle'])
            tempSat = Satellite(time.time(),data['above'][i]['satid'],satdata['tle'])
            
            if tempSat not in satList: # SAT is not in list, add to list and publish mqtt
                satList.append(tempSat)
                sendSatMQTT(satdata)
            
        print("Stored Satdata: "+str(len(satList)))
        #print(len(satList))

        satelliteTimeouts()

        #store satellites in buffer, only send new satellites. clear buffer after some time

        #send new sats via mqtt, e.g.:
        #sendSatMQTT("NW", 134)

        
        time.sleep(API_FETCH_TIMEOUT)

def sendSatMQTT(satdata):
    speed = 100
    direction = 0
    tle_split = satdata['tle'].split()

    direction = calculateAzimuth(float(tle_split[12]))
    speed = int(float(tle_split[15])) #close enough

    print("--> New Sat detected: Publishing MQTT Message to topic 'satlight/sat'\n")
    mqttc.publish(MQTT_TOPIC, str(direction) + '#' + str(speed) + '#')

    #print(tle_split)


def satelliteTimeouts():
    #for attr, value in satList.__dict__.items():
    now = time.time()
    for sat in satList:
        #print(sat.satid)
        if sat.timestamp+SATBUFFER_TIMEOUT < now:
            print('A sat timed out, removing from buffer. ID: '+str(sat.satid))
            #print(sat.satid)
            satList.remove(sat)
    
    #print("Stored after removal:")
    #print(len(satList))
            

def calculateAzimuth(asc):
    #print(asc)
    if (asc > 0.0 and asc < 22.5) or (asc <= 360.0 and asc > 337.5):

        return "0" #N

    elif (asc > 22.5 and asc < 67.5):

        return "1" #NE
  
    elif (asc > 67.5 and asc < 112.5):
  
        return "2" #E
  
    elif (asc > 112.5 and asc < 157.5):
  
        return "3" #SE
  
    elif (asc > 157.5 and asc < 202.5):
  
        return "4" #S
  
    elif (asc > 202.5 and asc < 247.5):
  
        return "5" #SW
  
    elif (asc > 247.5 and asc < 292.5):
  
        return "6" #W
  
    elif (asc > 292.5 and asc < 337.5):
    
        return "7" #NW
  
    return "-1" #N/A

if __name__ == "__main__":
    main()
