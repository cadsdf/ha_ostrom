import requests
import json
import datetime
import base64
import math


class OstromApi:
    
    def __init__(self,user: str, pwd: str) -> None:
        """Initialise."""
        self.user = user
        self.pwd = pwd
        self.zip = "00000"
        auth_key_str = user + ":" + pwd
        auth_key = base64.b64encode(auth_key_str.encode("ascii"))
        self.apikey = auth_key.decode("ascii")
        
    #get a token - token expires normaly after 3600 secs. (base64_apikey)
    def ostrom_outh(self):    
        url = "https://auth.production.ostrom-api.io/oauth2/token"
        payload = {"grant_type": "client_credentials"}
        headers = {
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
            "authorization": "Basic " + self.apikey
        }
        response = requests.post(url, data=payload, headers=headers)
        if response.status_code == requests.codes.created:
            self.token = auth['token_type'] + " " + auth['access_token']
            self.expire = (datetime.datetime.utcnow() + datetime.timedelta(seconds = (int(auth['expires_in']) - 30)))
        else:
            err = str(response.status_code) + "#" + response.text
            raise APIAuthError("Auth error "+err)
            
    #  nr index contract id - normaly only 1 - so index 0 default
    def ostrom_contracts(self,nr=0):
        url = "https://production.ostrom-api.io/contracts"
        headers = {
            "accept": "application/json",
             "authorization": self.token
        }
        response = requests.get(url, headers=headers)
        if response.status_code == requests.codes.ok:
            cdat = json.loads(response.text)
            self.zip = cdat['data'][nr]['address']['zip']
            self.cid = str(cdat['data'][nr]['id'])
            #{'zip': 'postleitzahl', 'cid': 'vertragrsid'}
        else:
            err = str(response.status_code) + "#" + response.text
            
    def ostrom_ha_setup(self):
        ostrom_outh(self)
        ostrom_contracts(self)
        
    # forcast price maxinal data 36 hours and data are processed to "date" and enduser "price"
    # forcast hours (max 36)
    def ostrom_price(self, starttime, stunden = 36):
        tax = "grossKwhTaxAndLevies"
        kwprice = "grossKwhPrice"
        timeformat = "%Y-%m-%dT%H:00:00.000Z"
        now = starttime.strftime(timeformat)
        future = (starttime + datetime.timedelta(hours=stunden)).strftime(timeformat)
        url = "https://production.ostrom-api.io/spot-prices?startDate=" + now + "&endDate=" + future + "&resolution=HOUR&zip=" + zip
        headers = {
            "accept": "application/json",
            "authorization": self.token
        }
        response = requests.get(url, headers=headers)
        erg = json.loads(response.text)
        ok = (response.status_code == requests.codes.ok)
        japex = {"average":0 , "low" : {"date":"","price":100.0}, "data":[] }
        for ix in erg['data']:
            #gesamtpreis ermitteln
            jg = round(float(ix[tax]) + float(ix[kwprice]), 2)
            #minmalwert
            if  jg < japex["low"]["price"]:
                japex["low"]["date"] = ix['date']
                japex["low"]["price"] = jg
            # liste aufbauen
            japex["data"].append({'date': ix['date'],'price':jg})
            # summe aufaddieren
            japex['average'] = japex['average']+jg
        # durchschnitt
        japex['average'] = round(japex['average'] / len(japex['data']),2)
        return japex # json.dumps(japex)
       # one hour {"date":"string date.hour","price": powerprice}
       #{"average": price_average over data, "low": lowes Hour, "data": [{one hour},...]  
       
       # data hour : {"date": "string.datetime", "kWh": from_grid }
       #[{data_hour},....] start at 0:00 , end 23:00 selected day in past.
    def ostrom_consum(self, daypast=2):
        timeformat = "%Y-%m-%dT00:00:00.000Z" #ganze tage
        dvon = (datetime.datetime.utcnow() - datetime.timedelta(days=daypast)).strftime(timeformat)
        dbis = (datetime.datetime.utcnow() - datetime.timedelta(days=(daypast-1))).strftime(timeformat)
        url = "https://production.ostrom-api.io/contracts/" + cid + "/energy-consumption?startDate=" + dvon + "&endDate=" + dbis + "&resolution=HOUR"
        headers = {
            "accept": "application/json",
            "authorization": self.token
        }
        response = requests.get(url, headers=headers)
        ok = (response.status_code == requests.codes.ok)
        if response.status_code == requests.codes.ok:
            erg = json.loads(response.text)
            tsum = 0
            for lo in erg["data"]:
                #print(lo)
                tsum = tsum + lo["kWh"]
            erg["daysum"]=tsum
        else:
            erg= {"err" : str(response.status_code) + "#" + response.text}
        return erg #json.dumps(erg['data'])
        
    def get_forecast_prices(self):
        jetzt = datetime.datetime.utcnow()
        if self.expire > jetzt:
            self.ostrom_outh()
        daten = self.ostrom_price(self, datetime.datetime.utcnow(), stunden = 36)
        return daten
        
    def get_past_price_consum(self):
        jetzt = datetime.datetime.utcnow()
        if self.expire > jetzt:
            self.ostrom_outh()
        

    
class APIAuthError(Exception):
    """Exception class for auth error."""


class APIConnectionError(Exception):
    """Exception class for connection error."""
