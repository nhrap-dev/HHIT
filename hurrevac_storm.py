# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 09:36:01 2020
Requirements: Python 3.7, Anaconda3 64bit
@author: Colin Lindeman
"""

import tkinter as tk
import tkinter.ttk as ttk
import pandas as pd
import numpy as np
import json
import math
from math import radians, cos, sin, asin, sqrt 

def popupmsg(msg):
    NORM_FONT= ("Tahoma", 12)
    popup = tk.Toplevel()
    popup.wm_title("!")
    label = ttk.Label(popup, text=msg, font=NORM_FONT)
    label.pack(side="top", fill="x", pady=10)
    B1 = ttk.Button(popup, text="Okay", command = popup.destroy)
    B1.pack()
    popup.mainloop() 

def processStormJSON(inputJSON):
    try:
        def distance(lat1, lat2, lon1, lon2): 
            # The math module contains a function named 
            # radians which converts from degrees to radians. 
            lon1 = radians(lon1) 
            lon2 = radians(lon2) 
            lat1 = radians(lat1) 
            lat2 = radians(lat2) 
            # Haversine formula  
            dlon = lon2 - lon1  
            dlat = lat2 - lat1 
            a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
            c = 2 * asin(sqrt(a))  
            # Radius of earth in 6371 kilometers. Use 3956 for miles 
            r = 3956
            # calculate the result 
            return(c * r) 
        
        def calculate_initial_compass_bearing(pointA, pointB):
            """
            https://gist.github.com/jeromer/2005586
            Calculates the bearing between two points.
            The formulae used is the following:
                θ = atan2(sin(Δlong).cos(lat2),
                          cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(Δlong))
            :Parameters:
              - `pointA: The tuple representing the latitude/longitude for the
                first point. Latitude and longitude must be in decimal degrees
              - `pointB: The tuple representing the latitude/longitude for the
                second point. Latitude and longitude must be in decimal degrees
            :Returns:
              The bearing in degrees
            :Returns Type:
              float
            """
            if (type(pointA) != tuple) or (type(pointB) != tuple):
                raise TypeError("Only tuples are supported as arguments")
            lat1 = math.radians(pointA[0])
            lat2 = math.radians(pointB[0])
            diffLong = math.radians(pointB[1] - pointA[1])
            x = math.sin(diffLong) * math.cos(lat2)
            y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1)
                    * math.cos(lat2) * math.cos(diffLong))
            initial_bearing = math.atan2(x, y)
            # Now we have the initial bearing but math.atan2 return values
            # from -180° to + 180° which is not what we want for a compass bearing
            # The solution is to normalize the initial bearing as shown below
            initial_bearing = math.degrees(initial_bearing)
            compass_bearing = (initial_bearing + 360) % 360
            return compass_bearing
        
        '''Load variables from the settings file'''
        with open(r".\hurrevac_settings.json") as f:
            hurrevacSettings = json.load(f)
        HurrevacRHurr50Factor = hurrevacSettings['HurrevacRHurr50Factor']
        HurrevacRHurr64Factor = hurrevacSettings['HurrevacRHurr64Factor']
        HurrevacVmaxFactor = hurrevacSettings['HurrevacVmaxFactor']
        HurrevacKnotToMphFactor = hurrevacSettings['HurrevacKnottoMphFactor']
        jsonColumns = hurrevacSettings['jsonColumns']
        
        '''Set to false to not perform any threshold checks on advisory or forecast points'''
        thresholdCheck = True
        
        '''Create dataframe for input when passing from hurrevac_main.py where it is stored as a dictionary from json...'''
        dfJSON = pd.DataFrame(inputJSON)
        # Filter the JSON by selecting which fields to keep...
        df = dfJSON[jsonColumns].copy()
        
        
        
        '''CALCULATE huStormTrack FIELDS for advisory (non-forecast) points...'''
        '''huStormTrackPtID'''
        #assigns a number sequentially starting from row 0. The rows should already be sorted by time asc
        startNumber = 1
        endNumber = len(df) + 1
        df.insert(0, 'huStormTrackPtID', range(startNumber, endNumber))
        #see also forecast section
        
        '''huScenarioName'''
        # Get the greatest dateTime row (last advisory)...
        maxAdvisory = df.loc[df['dateTime'].idxmax()]
        #Only get last advisories info to avoid issues with name changes and typoes (i.e. HARVEY, Harvey, TropicalDepression19)
        df['huScenarioName'] = maxAdvisory['stormName'] + "_Adv_" + maxAdvisory['number'] + "_" + maxAdvisory['stormId'][:2].upper() + maxAdvisory['stormId'][-4:]
    
        '''PointIndex'''
        df['PointIndex'] = np.nan
        
        '''TimeStep'''
        df['dateTime'] = pd.to_datetime(df['dateTime'], unit='ms')
        df['startDateTime'] = df['dateTime'].iloc[0] #get the first row's datatime value for new field
        df['TimeStep'] = df['dateTime'] - df['startDateTime']
        df['TimeStep'] = df['TimeStep'] / np.timedelta64(1,'h')
        df['TimeStep'] = df['TimeStep'].apply(np.int64)
        
        '''Latitude'''
        df.rename(columns = {'centerLatitude':'Latitude'}, inplace=True)
    
        '''Longitude'''
        df.rename(columns = {'centerLongitude':'Longitude'}, inplace=True)
        
        '''TranslationSpeed'''
        df['TranslationSpeed'] = 0
        #see also forecast section
        
        # '''TranslationSpeed'''
        # #read speed in nautical miles directly for advisory points
        # def translationSpeedCalc(row):
        #     speedKnots = row['speed']
        #     speedMph = speedKnots * HurrevacKnotToMphFactor
        #     return speedMph
        # df['TranslationSpeed'] = df.apply(lambda row: translationSpeedCalc(row), axis=1)
        # #see also forecast section
    
        '''RadiusToMaxWinds'''
        df['RadiusToMaxWinds'] = 0
        
        '''MaxWindSpeed'''
        def MaxWindSpeedCalc(row):
            currentForecastDict = row['currentForecast']
            maxWinds = currentForecastDict['maxWinds']
            maxWindsMPH = maxWinds * HurrevacKnotToMphFactor
            maxWindsMPHHVF = maxWindsMPH * HurrevacVmaxFactor
            return maxWindsMPHHVF
        df['MaxWindSpeed'] = df.apply(lambda row: MaxWindSpeedCalc(row), axis=1)
        
        '''Central Presssure'''
        df.rename(columns = {'minimumPressure':'CentralPressure'}, inplace=True)
        #see also forecast section
        
        '''ProfileParameter'''
        #pass
        
        '''RadiusToXWinds'''        
        def Mean_(*args):
            try:
                mean = sum(args) / len(args)
                return mean
            except ZeroDivisionError:
                print("Cannot divide by zero")
                return None
        
        def RadiusToXWinds(WindFields, windCat, RHurrXFactor):
            if len(WindFields['windFields']) > 0:
                windCats = []
                for x in WindFields['windFields']:
                    windCats.append(int(x['windSpeed']))
                if windCat in windCats:
                    for x in WindFields['windFields']:
                        if int(x['windSpeed']) == windCat:
                            radiiMean = Mean_(x['extent']['northEast'], x['extent']['southEast'], x['extent']['northWest'], x['extent']['southWest'])
                            value = (radiiMean * HurrevacKnotToMphFactor) * RHurrXFactor
                            return value         
                else:
                    return 0.0
            else:
                return 0.0
        
        def AdvisoryPointRadiusToXWinds(row, windCat, RHurrXFactor):
            currentForecastDict = row['currentForecast']
            return RadiusToXWinds(currentForecastDict, windCat, RHurrXFactor)
        
        #Caculate all wind radii...
        df['RadiusTo34KWinds'] = df.apply(lambda row: AdvisoryPointRadiusToXWinds(row, 34, 1), axis=1)
        df['RadiusTo50KWinds'] = df.apply(lambda row: AdvisoryPointRadiusToXWinds(row, 50, HurrevacRHurr50Factor), axis=1)
        df['RadiusToHurrWinds'] = df.apply(lambda row: AdvisoryPointRadiusToXWinds(row, 64, HurrevacRHurr64Factor), axis=1)
        
        #Zero out wind radii based on maxwindspeed...
        try:
            for i in range(0, len(df)):
                '''this requires that maxwindspeed is in mph and has hurrevac vmax factor applied'''
                CurrentMaxWindSpeed = df.loc[i, 'MaxWindSpeed']
                if CurrentMaxWindSpeed <= 57:
                    df.loc[i, 'RadiusTo50KWinds'] = 0
                    df.loc[i, 'RadiusToHurrWinds'] = 0
                elif CurrentMaxWindSpeed > 57 and CurrentMaxWindSpeed < 74:
                    df.loc[i, 'RadiusTo34KWinds'] = 0
                    df.loc[i, 'RadiusToHurrWinds'] = 0
                elif CurrentMaxWindSpeed >= 74:
                    df.loc[i, 'RadiusTo34KWinds'] = 0
                    df.loc[i, 'RadiusTo50KWinds'] = 0
                else:
                    pass
        except Exception as e:
            print('Wind Radii Cleanup', e)
    
        '''NewCentralPressure'''
        #pass
        
        '''NewTranslationSpeed'''
        #pass
        
        '''WindSpeedFactor'''
        #pass
        
        '''bInland'''
        df['bInland'] = 0
        #see also forecast section
        
        '''bForecast'''
        df['bForecast'] = 0
        #see also forecast section
        
        '''RadiusToHurrWindsType''' 
        #use maxwind*reductionfactor in mph to determine
        def radiusToHurrWindsType(row):
            MaxWindSpeedMPH = row['MaxWindSpeed']
            if MaxWindSpeedMPH <= 57:
                return "T"
            elif MaxWindSpeedMPH > 57 and MaxWindSpeedMPH < 74:
                return "5"
            elif MaxWindSpeedMPH >= 74:
                return "H"
            else:
                return np.nan
        try:
            df['RadiusToHurrWindsType'] = df.apply(lambda row: radiusToHurrWindsType(row), axis=1)
        except Exception as e:
            print('RadiusToHurrWindsType issue', e)
        
        '''NewRadiusToHurrWinds'''
        #pass
        
        '''NewRadiusTo50KWinds'''
        #pass
        
        '''NewRadiusTo34KWinds'''
        #pass
        


        '''FORECAST POINTS OF LAST ADVISORY, CALCULATE FIELDS...'''
        maxAdvisory = df.loc[df['dateTime'].idxmax()]
        dfForecasts = pd.json_normalize(maxAdvisory['futureForecasts'])
        if dfForecasts.size > 0:
            '''Rename the columns to match the main dataframe schema...'''
            dfForecasts.rename(columns = {'latitude':'Latitude',\
                                          'longitude':'Longitude',\
                                          'maxWinds':'MaxWindSpeed',\
                                          'hour':'dateTime'}, inplace=True)
            
            #Set forecast point values from last advisories values...
            dfForecasts['bForecast'] = 1
            dfForecasts['advisoryId'] = maxAdvisory['advisoryId']
            dfForecasts['stormName'] = maxAdvisory['stormName']
            dfForecasts['stormId'] = maxAdvisory['stormId']
            dfForecasts['huScenarioName'] = maxAdvisory['huScenarioName']
            dfForecasts['RadiusToMaxWinds'] = maxAdvisory['RadiusToMaxWinds']
            dfForecasts['number'] = maxAdvisory['number']
            
            '''huStormTrackPtID'''
            startNumber = int(maxAdvisory['huStormTrackPtID']) + 1
            endNumber = int(maxAdvisory['huStormTrackPtID']) + len(dfForecasts)+1
            dfForecasts.insert(0, 'huStormTrackPtID', range(startNumber, endNumber))
        
            '''timeStep'''
            dfForecasts['dateTime'] = dfForecasts['dateTime'].astype('datetime64[ms]')
            dfForecasts['startDateTime'] = maxAdvisory['startDateTime']
            dfForecasts['TimeStep'] = dfForecasts['dateTime'] - dfForecasts['startDateTime']
            dfForecasts['TimeStep'] = dfForecasts['TimeStep'] / np.timedelta64(1,'h')
            dfForecasts['TimeStep'] = dfForecasts['TimeStep'].apply(np.int64)
            dfForecasts.drop(columns=['startDateTime'], inplace=True)
        
            '''MaxWindSpeed'''
            def MaxWindSpeedForecastCalc(row):
                maxWinds = row['MaxWindSpeed']
                maxWindsMPH = maxWinds * HurrevacKnotToMphFactor
                maxWindsMPHHVF = maxWindsMPH * HurrevacVmaxFactor
                return maxWindsMPHHVF
            dfForecasts['MaxWindSpeed'] = df.apply(lambda row: MaxWindSpeedCalc(row), axis=1)
        
            '''RadiusToXWinds'''
            dfForecasts['RadiusTo34KWinds'] = dfForecasts.apply(lambda row: RadiusToXWinds(row, 34, 1), axis=1)
            dfForecasts['RadiusTo50KWinds'] = dfForecasts.apply(lambda row: RadiusToXWinds(row, 50, HurrevacRHurr50Factor), axis=1)
            dfForecasts['RadiusToHurrWinds'] = dfForecasts.apply(lambda row: RadiusToXWinds(row, 64, HurrevacRHurr64Factor), axis=1)
            
            '''RadiusToHurrWindsType'''
            try:
                dfForecasts['RadiusToHurrWindsType'] = dfForecasts.apply(lambda row: radiusToHurrWindsType(row), axis=1)
            except Exception as e:
                print('forecast radiustohurrwindstyp', e)
        
            '''Translation Speed'''
            dfForecasts['TranslationSpeed'] = 0
            
            # '''Translation Speed'''
            # #speed in mph from advisory point to forecast point 0, etc...
            # dfForecasts['distance'] = np.nan
            # dfForecasts['TranslationSpeed'] = np.nan
            # #set default point...
            # latA = maxAdvisory['Latitude']
            # longA = maxAdvisory['Longitude']
            # for i in range(0, len(dfForecasts)):
            #     latB = dfForecasts.loc[i, 'Latitude']
            #     longB = dfForecasts.loc[i, 'Longitude']
            #     distanceMiles = distance(latA, latB, longA, longB)
            #     dfForecasts.loc[i, 'distance'] = distanceMiles
            #     #set beginning point to previous forecast point for next loop...
            #     latA = latB
            #     longA = longB
            # timeA = maxAdvisory['TimeStep']
            # for i in range(0, len(dfForecasts)):
            #     timeB = dfForecasts.loc[i, 'TimeStep']
            #     timeHours = timeB - timeA
            #     distanceMiles = dfForecasts.loc[i, 'distance']
            #     speedMPH = distanceMiles / timeHours
            #     dfForecasts.loc[i, 'TranslationSpeed'] = speedMPH
            #     #set beginning point to previous forecast point for next loop...
            #     timeA = timeB
            
            '''direction'''
            dfForecasts['direction'] = np.nan
            #set default point...
            latA = maxAdvisory['Latitude']
            longA = maxAdvisory['Longitude']
            for i in range(0, len(dfForecasts)):
                latB = dfForecasts.loc[i, 'Latitude']
                longB = dfForecasts.loc[i, 'Longitude']
                #create point tuple...
                pointA = (float(latA), float(longA))
                pointB = (float(latB), float(longB))
                compassBearing = calculate_initial_compass_bearing(pointA, pointB)
                dfForecasts.loc[i, 'direction'] = compassBearing
                #set beginning point to previous forecast point for next loop...
                latA = latB
                longA = longB
            
            '''CentralPressure'''
            try:
                pressureBar = 1013.0
                dfForecasts['CentralPressure'] = np.nan
                #set default point...
                cpA = maxAdvisory['CentralPressure']
                mwsA = maxAdvisory['MaxWindSpeed']
                for i in range(0, len(dfForecasts)):
                    mwsB = dfForecasts.loc[i, 'MaxWindSpeed']
                    if mwsA <= 0:
                        #this needs to be reworked to not stop if initial mwsA is 0!
                        pass
                    else:
                        cpB = (pressureBar - (pressureBar - cpA) * (mwsB/mwsA)**2)
                        cpB = int(cpB + 0.5)
                        dfForecasts.loc[i, 'CentralPressure'] = cpB
                        #set beginning point to previous forecast point for next loop...
                        cpA = cpB
                        mwsA = mwsB
            except Exception as e:
                print('forecast centralPressure:')
                print(e)
            
            '''bInland'''
            def TESTforecastInland(row):
                try:
                    status = row['status']
                    if status:
                        if 'inland' in status.lower():
                            return 1
                        else:
                            return 0
                    else:
                        return 0
                except Exception as e:
                    print('Exception: forecast inland')
                    print(e)
            dfForecasts['bInland'] = dfForecasts.apply(lambda row: TESTforecastInland(row), axis=1) 
            
            
            
            '''CLEANUP THE FORECASTS DATAFRAME TO APPEND TO THE MAIN DATAFRAME...'''
            '''Format the forecasts before appending...'''
            dfForecasts = dfForecasts[['number',\
                                       'huStormTrackPtID',\
                                        'huScenarioName',\
                                        'TimeStep',\
                                        'Latitude',\
                                        'Longitude',\
                                        'TranslationSpeed',\
                                        'RadiusToMaxWinds',\
                                        'MaxWindSpeed',\
                                        'CentralPressure',\
                                        'RadiusToHurrWinds',\
                                        'RadiusTo50KWinds',\
                                        'RadiusTo34KWinds',\
                                        'bInland',\
                                        'bForecast',\
                                        'RadiusToHurrWindsType',\
                                        'advisoryId',\
                                        'stormName',\
                                        'stormId',\
                                        'dateTime']]
            dfForecasts = dfForecasts.sort_values(by='dateTime', ascending=True)
        
            '''APPEND forecast records to main dataframe...'''
            df = df.append(dfForecasts, ignore_index=True)
            
            
            
        '''THRESHOLD CHECKS AND DATA CONDITIONING...'''
        if thresholdCheck:
            '''If lat,long is 0,0; delete the row'''
            df = df.loc[(df['Latitude'] != 0) & (df['Longitude'] != 0)]            
            
            '''Only for interim (i.e. 4A), Where ever there is a 0 or null, use previous'''
            for fieldName in ['RadiusToHurrWinds',\
                              'RadiusTo50KWinds',\
                              'RadiusTo34KWinds']:
                previous = None
                for i in df.index:
                    current = df.loc[i, fieldName]
                    numberValue = str(df.loc[i, 'number'])
                    if i == 0:
                        '''First row won't have a previous'''
                        pass
                    else:
                        if 'A' in numberValue.upper():
                            if current == 0:
                                df.loc[i, fieldName] = previous
                            else:
                                pass
                        else:
                            pass
                    previous = current
                    
            '''For all'''
            def ThresholdMaxWindSpeed(row):
                '''this requires that maxwindspeed is in mph and has hurrevac vmax factor applied'''
                MaxWindSpeedValue = row['MaxWindSpeed']
                if MaxWindSpeedValue < 40:
                    return 40
                else:
                    return MaxWindSpeedValue
            df['MaxWindSpeed'] = df.apply(lambda row: ThresholdMaxWindSpeed(row), axis=1) 
            
            def ThresholdRadiusTo34KWinds(row):
                if row['MaxWindSpeed'] < 58 and row['RadiusTo34KWinds'] == 0:
                    return 30
                else:
                    return row['RadiusTo34KWinds']
            df['RadiusTo34KWinds'] = df.apply(lambda row: ThresholdRadiusTo34KWinds(row), axis=1) 
        


        '''TRIM and FORMAT the dataframe to match the HAZUS tables...'''
        df_huStormTrack = df[['huStormTrackPtID',\
                        'huScenarioName',\
                        'PointIndex',\
                        'TimeStep',\
                        'Latitude',\
                        'Longitude',\
                        'TranslationSpeed',\
                        'RadiusToMaxWinds',\
                        'MaxWindSpeed',\
                        'CentralPressure',\
                        'RadiusToHurrWinds',\
                        'RadiusTo50KWinds',\
                        'RadiusTo34KWinds',\
                        'bInland',\
                        'bForecast',\
                        'RadiusToHurrWindsType']]
            
            
            
        '''CREATE huScenario TABLE...'''
        df_huScenarioName = df['huScenarioName']
        df_huScenario = df_huScenarioName.drop_duplicates().to_frame() #Not sure if this is the best method to get a list of one...
        df_huScenario['bSSCurrent'] = 0
        df_huScenario['bTimeStep'] = 0
        df_huScenario['bTranslationSpeed'] = 0
        df_huScenario['bMaxWindSpeed'] = 1
        df_huScenario['bCentralPressure'] = 1
        df_huScenario['bProfileParameter'] = 0
        df_huScenario['bRadiusType'] = 0
        df_huScenario['Info'] = "HURREVAC HVX Storm Advisory Download;" + maxAdvisory['stormName'] + " " + maxAdvisory['stormId']
        df_huScenario['Type'] = 4
        
        
        
        '''RETURN THE THREE OBJECTS...'''
        huScenarioName = df_huScenario['huScenarioName'].unique().tolist()[0]
        huStormTrack = df_huStormTrack
        huScenario = df_huScenario
        return huScenarioName, huScenario, huStormTrack
    
    except Exception as e:
        print(e)
        popupmsg('Error processing Storm JSON. Check your stormid.')
    
            
#Test some of the code above...
# if __name__ == "__main__":
#     myclass = Hurrevac()