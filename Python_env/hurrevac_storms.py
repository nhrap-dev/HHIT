# -*- coding: utf-8 -*-
"""
Created on Mon Apr 20 09:36:01 2020
Requirements: Python 3.7, Anaconda3 64bit
@author: Colin Lindeman
"""

import json
#import logging
import os
import requests
import socket
from subprocess import call
import time
import tkinter as tk
import tkinter.ttk as ttk

from Python_env import hurrevac_storm


try:
    with open("hurrevac_settings.json") as f:
        hurrevacSettings = json.load(f)
except:
    with open("./Python_env/hurrevac_settings.json") as f:
        hurrevacSettings = json.load(f)
    
def popupmsg(msg):
    """ Creates a tkinter popup message window

        Keyword Arguments:
            msg: str -- The message you want to display
    """    
    tk.messagebox.showinfo(message=msg)
##    logging.debug("Running popupmsg")

def get_key(val, my_dict):
    """ Check if a given value exists in a dictionary and
        return it's key pairing

        Keyword Arguments:
            val: dictionary value
            my_dict: dictionary

        Returns:
            key: string?
    """    
    for key, value in my_dict.items(): 
         if val == value: 
             return key 
    return "key doesn't exist"

class Manage:
    def __init__(self):
        try:
            with open('./src/config.json') as configFile:
                self.config = json.load(configFile)
        except:
            with open('../src/config.json') as configFile:
                self.config = json.load(configFile)
        # environmental variables
        self.proxy = self.config['proxies']['fema']
        self.release = self.config['release']
        self.http_timeout = self.config[self.release]['httpTimeout']  # in seconds
    
    def setProxies(self):
        """ Temporarily updates the local environmental variables with updated proxies
        """
        call('set HTTP_PROXY=' + self.proxy, shell=True)
        call('set HTTPS_PROXY=' + self.proxy, shell=True)
        os.environ["HTTP_PROXY"] = self.proxy
        os.environ["HTTPS_PROXY"] = self.proxy

    def handleProxy(self):
        try:
            who_am_i = os.popen('whoami').read().split('\\')[0]
            if who_am_i.lower() == 'fema':
                self.setProxies()
                return True
            else:
                return False
        except:
            # 0 indicates there is no internet connection
            # or the method was unable to connect using the hosts and ports
            return -1

class StormsInfo:
    def __init__(self):
        ''' '''
        self.GetStormsJSON()
        self.GetStormsTypes()
        self.GetStormsYears()
        self.GetStormsBasins()
    
    def GetStormsJSON(self):
        """ Populates JSON variable with json storms data from Hurrevac url\
        
        Notes:
            TODO the app crashes if no internet or the hurrevac hvx api website is down
        """
##        logging.debug("Running GetStormsJSON")
        manage = Manage()
        manage.handleProxy()
        for attempt in range(3):
            try:
                openUrl = requests.get(hurrevacSettings['HurrevacStormsURL'], timeout=10)
            except:
                time.sleep(2)
                continue
            else:
                break
        else:
            print("Error receiving data")
        if(openUrl.status_code == 200):
            stormsJSON = openUrl.json()
            self.JSON = stormsJSON
        else:
            print(f"Error GetStormsJSON: {openUrl.status_code}")
            
    def GetStormsTypes(self):
        """ Populates the storm types dropdown
        """
##        logging.debug("Running GetStormsTypes")
        StormTypes = hurrevacSettings['ShowStormTypes']
        StormTypesList = []
        for key in StormTypes.keys():
            if StormTypes[key]:
                StormTypesList.append(key)
        StormTypesList.sort()
        self.types = tuple(StormTypesList)

    def GetStormsBasins(self):
        """ Populates the storm basins dropdown
        """
##        logging.debug("Running GetStormsBasins")
        StormBasins = hurrevacSettings['BasinsDictionary']
        StormBasinsLabels = list(StormBasins.values())
        self.basins = tuple(StormBasinsLabels)

    def GetStormsYears(self):
        """ Populates the storm years dropdown
        """
##        logging.debug("Running GetStormsYears")
        yearList = []
        for i in self.JSON:
            try:
                year = int(i)
            except:
                year = i
            yearList.append(year)
        yearList.sort(reverse=True)
        self.years = tuple(yearList)
    
    def GetStormNames(self, stormTypes, basinLabel, year):
        """ Acquires the names of storms from Hurrevac json data

        Keyword Arguments:
           stormTypes : tuple
           basinLabel : tuple
           year: tuple
            
        Returns:
           stormNameStatusIDList : tuple

        Note: There is logic to include/exclude and sort storms based on
        basin, type and status.
        """
        
##        logging.debug("Running GetStormNames")
        '''Get basins code from label in settings.json'''
        StormBasins = hurrevacSettings['BasinsDictionary']
        basinCode = get_key(basinLabel, StormBasins)
        stormNameStatusIDList = []
        
        activeStormsDictList = []
        historicStormsDictList = []
        exerciseStormsDictList = []
        simulatedStormsDictList = []
        
        activeStormsLabelsList = []
        historicStormsLabelsList = []
        exerciseStormsLabelsList = []
        simulatedStormsLabelsList = []
        
        '''Iterate over storms for a given year, append to each list'''
        try:
            year = str(year)
        except:
            year = year
        for storm in self.JSON[year]:
            stormName = str(storm['name'])
            stormId = str(storm['stormId'])
            stormStatus = str(storm['status'])
            stormBasin = str(storm['basin'])
            stormDict = {"Name":stormName,"Status":stormStatus,"StormId":stormId}
            if stormBasin == basinCode:
                if stormStatus == "Simulated":
                    simulatedStormsDictList.append(stormDict)
                elif stormStatus == "Historical":
                    historicStormsDictList.append(stormDict)
                elif stormStatus == "Exercise":
                    exerciseStormsDictList.append(stormDict)
                elif stormStatus == "Active":
                    activeStormsDictList.append(stormDict)
                    
        '''Sort the lists alphabetically by stormid:essentially by number i.e. ['al012020', 'al022020']'''
        def stormDictSortFunc(e):
            '''use to sort a list of dictionaries by a dictionaries key's value'''
            return e['StormId']
        activeStormsDictList.sort(key=stormDictSortFunc)
        historicStormsDictList.sort(key=stormDictSortFunc)
        exerciseStormsDictList.sort(key=stormDictSortFunc)
        simulatedStormsDictList.sort(key=stormDictSortFunc)

        '''Create the stormlabels to be shown in the gui'''
        for storm in activeStormsDictList:
            stormName = str(storm['Name'])
            stormStatus = str(storm['Status'])
            stormId = str(storm['StormId'])
            stormLabel = stormName + " (" + stormStatus + ") " + " [" + stormId + "]"
            activeStormsLabelsList.append(stormLabel)
        for storm in historicStormsDictList:
            stormName = str(storm['Name'])
            stormStatus = str(storm['Status'])
            stormId = str(storm['StormId'])
            stormLabel = stormName + " (" + stormStatus + ") " + " [" + stormId + "]"
            historicStormsLabelsList.append(stormLabel)
        for storm in exerciseStormsDictList:
            stormName = str(storm['Name'])
            stormStatus = str(storm['Status'])
            stormId = str(storm['StormId'])
            stormLabel = stormName + " (" + stormStatus + ") " + " [" + stormId + "]"
            exerciseStormsLabelsList.append(stormLabel)
        for storm in simulatedStormsDictList:
            stormName = str(storm['Name'])
            stormStatus = str(storm['Status'])
            stormId = str(storm['StormId'])
            stormLabel = stormName + " (" + stormStatus + ") " + " [" + stormId + "]"
            simulatedStormsLabelsList.append(stormLabel)
        
        '''Determine which type of storms are added to the main list'''
        if 'Active' in stormTypes:
            for i in activeStormsLabelsList:
                stormNameStatusIDList.append(i)
        if 'Historical' in stormTypes:
            for i in historicStormsLabelsList:
                stormNameStatusIDList.append(i)
        if 'Exercise' in stormTypes:
            for i in exerciseStormsLabelsList:
                stormNameStatusIDList.append(i)
        if 'Simulated' in stormTypes:
            for i in simulatedStormsLabelsList:
                stormNameStatusIDList.append(i)
        if len(stormNameStatusIDList) > 0:
            return tuple(stormNameStatusIDList)
        else:
            return ('No Storms Found',)

class StormInfo:
    def GetStormJSON(self, StormId):
        """ Acquires an individual storms Hurrevac JSON data

        Keyword Arguments:
           StormId :string -- Hurrevac stormid

        Notes: 
            https://hvx.hurrevac.com/hvx-api/v1/advisories/storm/{stormidhere has storms and
            empty json for simulated storms.
            https://hvx.hurrevac.com/hvx-api/v1/sim/advisories/storm/{stormidhere} has simulated storms and
            empty json for non-simulated storms.
        """
        self.Id = StormId
        manage = Manage()
        manage.handleProxy()

        url_list = []
        url_list.append(hurrevacSettings['HurrevacActiveStormURL'] + StormId)
        url_list.append(hurrevacSettings['HurrevacHistoricStormURL'] + StormId)
        url_list.append(hurrevacSettings['HurrevacExerciseStormURL'] + StormId)
        url_list.append(hurrevacSettings['HurrevacSimulatedStormURL'] + StormId)

        url_list_unique = list(set(url_list))

        url_valid_list = []
        for url in url_list_unique:
            openUrl = requests.get(url, timeout=10)
            if(openUrl.status_code == 200):
                url_valid_list.append(url)

        if len(url_valid_list) > 0:
            for url in url_valid_list:
                openUrl = requests.get(url, timeout=10)
                stormJSON = openUrl.json()
                if len(stormJSON) > 0:
                    self.JSON = stormJSON
                    break
            else:
                popupmsg("StormID not found.")
                print(f"StormID data not found in {url_valid_list}")
##              logging.warning("stormJSON length is 0, possible incorrect stormid")
        else:
            popupmsg("Error receiving data. Check settings.json url or site is down or changed.")
            print("Error receiving data: %s" % openUrl.status_code)
##          logging.error("Error receiving data: %s" % openUrl.status_code)

    def GetStormDataframe(self, stormJSON):
        """ Convert Hurrevac JSON of user's selected stormid into pandas dataframes using
            another script

        Keyword Arguments:
           stormJSON : json
        """
##        logging.debug("Running GetStormDataframe")
        stormDataframes = hurrevac_storm.processStormJSON(stormJSON)
        self.huScenarioName = stormDataframes[0]
        self.huScenario = stormDataframes[1]
        self.huStormTrack = stormDataframes[2]

#Test some of the code above...
if __name__ == "__main__":
    myclass = StormsInfo()
    
    print("all possible types from config:", myclass.types)
    print()
    print("all possible basins from config:", myclass.basins)
    print()
    print("all possible years from source:", myclass.years)
    print()
    print("Atlantic 2014 storm labels:", myclass.GetStormLabels('Atlantic', '2014'))
    print()
    print("Eastern Pacific 2020 storm labels:", myclass.GetStormLabels('Eastern Pacific', '2020'))
    print()
    print("Atlantic 2014 storm names:", myclass.GetStormNames(['Active', 'Historical', 'Exercise', 'Simulated'], 'Atlantic', '2014'))
    print()
    print("Eastern Pacific 2020 storm names:", myclass.GetStormNames(['Active', 'Historical', 'Exercise', 'Simulated'], 'Eastern Pacific', '2020'))
    print()

    storm1 = StormInfo()
    storm1.GetStormJSON("al012020")
    print(storm1.Id)
    storm1.GetStormDataframe(storm1.JSON)
    print(storm1.huScenario)
    print(storm1.huStormTrack)
    
