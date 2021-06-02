import datetime
import random
import requests
import time

# from apscheduler.schedulers.background import BackgroundScheduler

# Also gotta see what apps are actually able to be used (cameras online?)

# read in json
applist = list(requests.get("http://127.0.0.1:5000/apps").json().values())

collections = {}
playlist_base = []

for exp in applist:
    if 'collection' in exp:
        if exp['collection'] not in collections:
            playlist_base.append([exp['collection']])
            collections[exp['collection']] = [exp]

        else:
            collections[exp['collection']].append(exp)
    else:
        playlist_base.append([exp])
    


cont = True

def should_advance(start_time, app):
        current_app = requests.get("http://127.0.0.1:5000/current-app").json()
        if 'end_time' in current_app:
            if datetime.datetime.now() < datetime.datetime.fromtimestamp(current_app['end_time']):
                return False
        else:
            if ((datetime.datetime.now() - start_time).total_seconds() < app['lifetime']):
                return False

        return True

while cont:
    playlist = playlist_base
    random.shuffle(playlist)
    for app in playlist:    
        # app = appbase[1]

        if app in collections:
            app = random.choice(collections[app])

        r = requests.put("http://localhost:5000/current-app", headers={'Content-Type': 'application/json'}, json={'id': app['id'] })

        # print(r)

        current_app = list(requests.get("http://127.0.0.1:5000/current-app").json().items())
        start_time = datetime.datetime.now()
        advance = False

        # wait for confirmation that it's running?

        while(not advance):
            time.sleep(5)
            advance = should_advance(start_time, app)
        


        

    # check for new applist data? should it be able to be updated on the fly?

# do forever
    # while list isn't empty 
        # send id 
        # wait for amount of time
        # follow list
    # reshuffle after list empty 


    