import copy
import datetime
import random
from typing_extensions import runtime
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
commercial_base = []
last_exp = ""

for exp in explist:
    if "collection" in exp:
        if exp["collection"] == "commercials":
            commercial_base.append(exp)
        elif exp["collection"] not in collections:
            playlist_base.append(exp["collection"])
            collections[exp["collection"]] = [exp]
        else:
            collections[exp["collection"]].append(exp)
    else:
        playlist_base.append(exp)

collections_shuffle = copy.deepcopy(collections)

for collection in collections_shuffle:
    random.shuffle(collections_shuffle[collection])


def should_advance(start_time):
    current_exp = requests.get(CURRENT_ENDPOINT).json()

    if current_exp["lock"]:
        return False
    if "end_time" in current_exp and datetime.datetime.now() < datetime.datetime.fromtimestamp(current_exp["end_time"]):
        return False
    print("current time", flush=True)
    print(datetime.datetime.now().timestamp())
    print("endtime")
    try: 
        print(datetime.datetime.fromtimestamp(current_exp["end_time"]))
    except KeyError:
        pass 
    current_date = datetime.datetime.now().timestamp()
    if (current_date - start_time) < current_exp["lifetime"]:
        return False
    print("current_date - start_time")
    print(current_date - start_time)
    # print(str.format(current_date - start_time))

    # print("should advance returned True")

    return True

commercial_timer = datetime.datetime.now().timestamp()
# print(commercial_base)
while True:
    playlist = []
    commercials = copy.deepcopy(commercial_base)
    for exp in playlist_base:
        if exp in list(collections.keys()):
            if len(collections_shuffle[exp]) == 0:
                collections_shuffle[exp] = copy.deepcopy(collections[exp])
                random.shuffle(collections_shuffle[exp])
            playlist.append(collections_shuffle[exp].pop())
        else:
            playlist.append(exp)

    random.shuffle(playlist)
    random.shuffle(commercials)
    exp = None
    for exp2 in playlist: # exp
        if exp == None: # exp
            exp = exp2
            continue
        print("playing: " + exp["id"], flush=True)
        print("=== Up next is: " + exp2["id"], flush=True)

        # r = 
        requests.put(
            CURRENT_ENDPOINT,
            headers={"Content-Type": "application/json"},
            json={"id": exp["id"]},
        )
        # print(r)
        # print("=== played successfully")

        current_exp = requests.get(CURRENT_ENDPOINT).json()
        while not current_exp:
            time.sleep(1)
        last_exp = current_exp["id"]
        start_time = datetime.datetime.now().timestamp()
        advance = False

        # wait for confirmation that it's running?

        while not advance:
            time.sleep(1) # 1
            current_exp = requests.get(CURRENT_ENDPOINT).json()
            # print("test", flush=True)
            #print("le: " + last_exp, flush=True)
            # print("ce: " + current_exp["id"], flush=True)
            if last_exp != current_exp["id"]:
                print("exp is changed: ", flush=True)
                print("last exp= " + last_exp, flush=True)
                print("current exp= " +current_exp["id"], flush=True)
                start_time = datetime.datetime.now().timestamp()
                last_exp = current_exp["id"]
            advance = should_advance(start_time)
            print("commercial timer - now")
            print(commercial_timer - datetime.datetime.now().timestamp(), flush=True)
            if advance and (commercial_timer - datetime.datetime.now().timestamp() >= 30) and len(commercial_base) != 0:
                if len(commercials) == 0:
                    commercials = random.shuffle(copy.deepcopy(commercial_base))
                last_exp = commercials.pop()["id"]
                requests.put(
                    CURRENT_ENDPOINT,
                    headers={"Content-Type": "application/json"},
                    json={"id": last_exp},
                )
                print("played commerical: " + last_exp, flush=True)
                commercial_timer = datetime.datetime.now().timestamp()
            
        exp = exp2

    # check for new explist data? should it be able to be updated on the fly?
