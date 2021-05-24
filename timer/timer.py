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
    # print(playlist)
    for app in playlist:
        
        
        # scheduler.add_job(lambda : scheduler.print_jobs(), 'interval', minutes=app["lifetime"])
        # scheduler.add_job(lambda : print(app["id"]), 'interval', minutes=app["lifetime"])
        
        lifetime = 9
        if 'lifetime' in app:
            lifetime = app['lifetime']

        r = requests.put("http://localhost:5000/current-app", headers={'Content-Type': 'application/json'}, json={'id': app[1]['id'] })
        print(r)

        # wait for confirmation that it's running?
        start_time = datetime.datetime.now()
        while ((datetime.datetime.now() - start_time).total_seconds() < lifetime):
            time.sleep(10)
            # print("10 SECONDS HAVE PASSED")

    # check for new applist data? should it be able to be updated on the fly?

# do forever
    # while list isn't empty 
        # send id 
        # wait for amount of time
        # follow list
    # reshuffle after list empty 