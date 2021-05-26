import copy
import datetime
import random
import requests
import time

# from apscheduler.schedulers.background import BackgroundScheduler

# Also gotta see what apps are actually able to be used (cameras online?)

# read in json
applist = list(requests.get("http://127.0.0.1:5000/apps").json().items())

# send commands to controller

cont = True

while cont:
    playlist = applist
    random.shuffle(playlist)
    
    for appbase in playlist:    
        app = appbase[1]
        
        r = requests.put("http://localhost:5000/current-app", headers={'Content-Type': 'application/json'}, json={'id': app['id'] })
        # print(r)

        current_app = list(requests.get("http://127.0.0.1:5000/current-app").json().items())

        start_time = datetime.datetime.now()
        if 'endtime' in current_app:
            #use endtime
            while (datetime.datetime.now() < current_app['endtime']):
                time.sleep(2)
                current_app = list(requests.get("http://127.0.0.1:5000/current-app").json().items())
        else:
            # use lifetime
            while ((datetime.datetime.now() - start_time).total_seconds() < app['lifetime']):
                time.sleep(10)

        

        # wait for confirmation that it's running?
        

    # check for new applist data? should it be able to be updated on the fly?

# do forever
    # while list isn't empty 
        # send id 
        # wait for amount of time
        # follow list
    # reshuffle after list empty 