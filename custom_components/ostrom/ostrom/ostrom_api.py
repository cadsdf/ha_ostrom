import aiohttp
import json
import datetime
import base64
import math
import asyncio


class OstromApi:
    
    def __init__(self,user: str, pwd: str, haloop) -> None:
        """Initialise."""
        self.user = user
        self.pwd = pwd
        self.zip = "00000"
        self.loop = haloop
        auth_key_str = user + ":" + pwd
        auth_key = base64.b64encode(auth_key_str.encode("ascii"))
        self.apikey = auth_key.decode("ascii")
        
    #get a token - token expires normaly after 3600 secs. (base64_apikey)
    async def ostrom_outh(self):    
        url = "https://auth.production.ostrom-api.io/oauth2/token"
        payload = {"grant_type": "client_credentials"}
        headers = {
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
            "authorization": "Basic " + self.apikey
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=payload, headers=headers) as response:
                text = await response.text()
                if response.status != 201:
                    raise Exception(f"ostrom_outh failed: status={response.status}, body={text}")
                auth = json.loads(text)
                self.token = auth['token_type'] + " " + auth['access_token']
                self.expire = (datetime.datetime.utcnow() + datetime.timedelta(seconds = (int(auth['expires_in']) - 30)))
            
    #  nr index contract id - normaly only 1 - so index 0 default
    async def ostrom_contracts(self, nr=0):
        url = "https://production.ostrom-api.io/contracts"
        headers = {
            "accept": "application/json",
            "authorization": self.token
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                text = await response.text()
                cdat = json.loads(text)
                if response.status == 200:
                    self.zip = cdat['data'][nr]['address']['zip']
                    self.cid = str(cdat['data'][nr]['id'])
                
    # forcast price maxinal data 36 hours and data are processed to "date" and enduser "price"
    # forcast hours (max 36)
    async def ostrom_price(self, starttime, stunden = 36):
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
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                text = await response.text()
                erg = json.loads(text)
                japex = {"average":0 , "low" : {"date":"","price":100.0}, "data":[] }
                for ix in erg['data']:
                    #gesamtpreis ermitteln
                    total_price = round(float(ix[tax]) + float(ix[kwprice]), 2)
                    japex["average"] += total_price
                    #minmalwert
                    if  total_price < japex["low"]["price"]:
                        japex["low"]["date"] = ix['date']
                        japex["low"]["price"] = total_price
                    # liste aufbauen
                    japex["data"].append({'date': ix['date'],'price':jg})
                # durchschnitt
                japex['average'] = round(japex['average'] / len(japex['data']),2)
                return japex # json.dumps(japex)
                # one hour {"date":"string date.hour","price": powerprice}
                #{"average": price_average over data, "low": lowes Hour, "data": [{one hour},...]  
       
    async def ostrom_consum(self, starttime, stunden = 1):
        timeformat = "%Y-%m-%dT%H:00:00.000Z"
        dvon = starttime.strftime(timeformat)
        dbis = (starttime + datetime.timedelta(hours=stunden)).strftime(timeformat)
        url = "https://production.ostrom-api.io/contracts/" + cid + "/energy-consumption?startDate=" + dvon + "&endDate=" + dbis + "&resolution=HOUR"
        headers = {
            "accept": "application/json",
            "authorization": self.token
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                text = await response.text()
                ok = (response.status == 200)
                return erg
                
    async def get_forecast_prices(self):
        jetzt = datetime.datetime.utcnow()
        # Prüfe die Token-Gültigkeit:
        if not self.expire or self.expire < jetzt:
            await self.ostrom_outh()
        # Preise mit gültigem Token abfragen:
        daten = await self.ostrom_price(jetzt, stunden=36)
        return daten            
        
        
    async def get_past_price_consum(self):
        past = datetime.datetime.utcnow() - datetime.timedelta(days=2)
        jetzt = datetime.datetime.utcnow()   
        if not self.expire or self.expire < jetzt:
            await self.ostrom_outh()
            

        
        
        

    
class APIAuthError(Exception):
    """Exception class for auth error."""


class APIConnectionError(Exception):
    """Exception class for connection error."""