import copy
import datetime
import random
import requests
import time
import os
import urllib.parse


CONTROLLER_URL = (
    os.environ["FT_CONTROLLER_URL"]
    if "FT_CONTROLLER_URL" in os.environ
    else "http://localhost:8000"
)
EXPERIENCES_ENDPOINT = urllib.parse.urljoin(CONTROLLER_URL, "experiences")
CURRENT_ENDPOINT = urllib.parse.urljoin(CONTROLLER_URL, "current")

# Also gotta see what exps are actually able to be used (cameras online?)

# read in json
explist = list(requests.get(EXPERIENCES_ENDPOINT).json().values())

collections = {}
playlist_base = []
last_exp = ""

for exp in explist:
    if "collection" in exp:
        if exp["collection"] not in collections:
            playlist_base.append(exp["collection"])
            collections[exp["collection"]] = [exp]
        else:
            collections[exp["collection"]].append(exp)
    else:
        playlist_base.append(exp)

collections_shuffle = copy.deepcopy(collections)

for collection in collections_shuffle:
    random.shuffle(collections_shuffle[collection])


def should_advance(start_time, exp):
    current_exp = requests.get(CURRENT_ENDPOINT).json()

    if "end_time" in current_exp:
        if datetime.datetime.now() < datetime.datetime.fromtimestamp(
            current_exp["end_time"]
        ):
            return False
    else:
        current_date = datetime.datetime.now().timestamp()
        if (current_date - start_time) < exp["lifetime"]:
            return False

    return True


while True:
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
    for exp in playlist:

        r = requests.put(
            CURRENT_ENDPOINT,
            headers={"Content-Type": "application/json"},
            json={"id": exp["id"]},
        )
        # print(r)

        current_exp = list(requests.get(CURRENT_ENDPOINT).json().items())
        last_exp = current_exp["id"]
        start_time = datetime.datetime.now().timestamp()
        advance = False

        # wait for confirmation that it's running?

        while not advance:
            time.sleep(1)
            if last_exp != current_exp["id"]:
                start_time = datetime.datetime.now().timestamp()
            advance = should_advance(start_time, exp)

    # check for new explist data? should it be able to be updated on the fly?
