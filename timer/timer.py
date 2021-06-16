import copy
import datetime
import random
import os
import requests
import requests_unixsocket
import time
import urllib.parse

_PLACARD_SOCKETS_PATH = os.path.join(os.environ["XDG_RUNTIME_DIR"], "placard", "socket")
_domain_sockets_session = requests_unixsocket.Session()
_placard_escaped_url = (
            f"http+unix://{urllib.parse.quote_plus(_PLACARD_SOCKETS_PATH)}"
        )



# from apscheduler.schedulers.background import BackgroundScheduler

# Also gotta see what apps are actually able to be used (cameras online?)

# read in json
applist = list(requests.get("http://127.0.0.1:5000/apps").json().values())

collections = {}
playlist_base = []

for exp in applist:
    if 'collection' in exp:
        if exp['collection'] not in collections:
            playlist_base.append(exp['collection'])
            collections[exp['collection']] = [exp]
        else:
            collections[exp['collection']].append(exp)
    else:
        playlist_base.append(exp)

collections_shuffle = copy.deepcopy(collections)


for collection in collections_shuffle:
    random.shuffle(collections_shuffle[collection])

cont = True

def should_advance(start_time, app):
        current_app = requests.get("http://127.0.0.1:5000/current-app").json()
        if 'end_time' in current_app:
            _domain_sockets_session.post(
                f"{_placard_escaped_url}/end-time",
                json={'end_time': current_app['end_time']},
            )
            print(current_app['end_time'])

            if datetime.datetime.now() < datetime.datetime.fromtimestamp(current_app['end_time']):
                return False
        else:
            end_time = start_time + (app['lifetime'])
            print("start_time")
            print(start_time)
            print("life")
            print(app['lifetime'])
            print("end")
            print(end_time)
            current_date = datetime.datetime.now().timestamp()
            _domain_sockets_session.post(
                f"{_placard_escaped_url}/end-time",
                json={'end_time': end_time},
            )
            if ((current_date - start_time) < app['lifetime']):
                return False

        return True

while cont:
    playlist = []
    for exp in playlist_base:
        if exp in list(collections.keys()):
            if len(collections_shuffle[exp]) == 0:
                collections_shuffle = copy.deepcopy(collections)
                random.shuffle(collections_shuffle[exp])
            playlist.append(collections_shuffle[exp].pop())
        else:
            playlist.append(exp)

    random.shuffle(playlist)
    for app in playlist:
            
        r = requests.put("http://localhost:5000/current-app", headers={'Content-Type': 'application/json'}, json={'id': app['id'] })

        # print(r)

        current_app = list(requests.get("http://127.0.0.1:5000/current-app").json().items())
        # start_time = (datetime.datetime.now() - datetime.datetime(1970,1,1)).total_seconds()
        start_time = datetime.datetime.now().timestamp()
        advance = False

        # wait for confirmation that it's running?

        while(not advance):
            time.sleep(1)
            advance = should_advance(start_time, app)
        


        

    # check for new applist data? should it be able to be updated on the fly?

# do forever
    # while list isn't empty 
        # send id 
        # wait for amount of time
        # follow list
    # reshuffle after list empty 


    