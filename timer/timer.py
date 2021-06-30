import copy
import datetime
import random
import requests
import time
import os
import urllib.parse


CONTROLLER_URL = os.environ["FT_CONTROLLER_URL"] if "FT_CONTROLLER_URL" in os.environ else "http://localhost:8000"
EXPERIENCES_ENDPOINT = urllib.parse.urljoin(CONTROLLER_URL, "current")
CURRENT_ENDPOINT = urllib.parse.urljoin(CONTROLLER_URL, "current")

# Also gotta see what apps are actually able to be used (cameras online?)

# read in json
applist = list(requests.get(EXPERIENCES_ENDPOINT).json().values())

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
        current_app = requests.get(CURRENT_ENDPOINT).json()
        if 'end_time' in current_app:
            if datetime.datetime.now() < datetime.datetime.fromtimestamp(current_app['end_time']):
                return False
        else:
            current_date = datetime.datetime.now().timestamp()
            if ((current_date - start_time) < app['lifetime']):
                return False

        return True


while cont:
    playlist = []
    for exp in playlist_base:
        if exp in list(collections.keys()):
            if len(collections_shuffle[exp]) == 0:
                collections_shuffle[exp] = copy.deepcopy(collections[exp])
                random.shuffle(collections_shuffle[exp])
            playlist.append(collections_shuffle[exp].pop())
        else:
            playlist.append(exp)

    random.shuffle(playlist)
    for app in playlist:
            
        r = requests.put(CURRENT_ENDPOINT, headers={'Content-Type': 'application/json'}, json={'id': app['id'] })
        # print(r)

        current_app = list(requests.get(CURRENT_ENDPOINT).json().items())
        start_time = datetime.datetime.now().timestamp()
        advance = False

        # wait for confirmation that it's running?

        while(not advance):
            time.sleep(1)
            advance = should_advance(start_time, app)
        


    # check for new applist data? should it be able to be updated on the fly?
