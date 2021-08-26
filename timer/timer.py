import copy
import datetime
dt = datetime.datetime
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
repeat = True
while repeat:
    try:
        explist = list(requests.get(EXPERIENCES_ENDPOINT).json().values())
        repeat = False
    except:
        print("failed to read in experience list")
        time.sleep(3)

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
        if exp["unlisted"]:
            continue
        playlist_base.append(exp)

collections_shuffle = copy.deepcopy(collections)

for collection in collections_shuffle:
    random.shuffle(collections_shuffle[collection])


def should_advance(start_time):
    current_exp = requests.get(CURRENT_ENDPOINT).json()
    # print("current time", flush=True)
    # print(dt.now())
    # print("endtime")
    # try: 
    #     print(dt.fromtimestamp(current_exp["end_time"]), flush=True)
    # except KeyError:
    #     pass 

    if current_exp["lock"]:
        return False
    current_date = dt.now()
    if "end_time" in current_exp:
        if current_date < dt.fromtimestamp(current_exp["end_time"]):
            return False   
    elif (current_date.timestamp() - start_time) < current_exp["lifetime"]:
        return False
    # print("current_date - start_time")
    # print(current_date.timestamp() - start_time)
    # print(str.format(current_date - start_time))

    # print("should advance returned True")

    return True

commercial_timer = dt.now().timestamp()
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
        start_time = dt.now().timestamp()
        advance = False

        # wait for confirmation that it's running?

        while not advance:
            time.sleep(1) # 1
            current_exp = requests.get(CURRENT_ENDPOINT).json()
            # print("test", flush=True)
            # print("le: " + last_exp, flush=True)
            # print("ce: " + current_exp["id"], flush=True)
            if last_exp != current_exp["id"]:
                print("exp is changed: ", flush=True)
                print("==last exp= " + last_exp, flush=True)
                print("==current exp= " + current_exp["id"], flush=True)
                start_time = dt.now().timestamp()
                last_exp = current_exp["id"]
            advance = should_advance(start_time)
            if advance and (dt.now().timestamp() - commercial_timer >= 90) and len(commercial_base) != 0:
                if len(commercials) == 0:
                    # print("shuffle com", flush=True)
                    commercials = copy.deepcopy(commercial_base)
                    random.shuffle(commercials)
                last_exp = commercials.pop()["id"]
                requests.put(
                    CURRENT_ENDPOINT,
                    headers={"Content-Type": "application/json"},
                    json={"id": last_exp},
                )
                print("played commerical: " + last_exp, flush=True)
                commercial_timer = dt.now().timestamp() # - current_exp["end_time"]
                advance = False
            
        exp = exp2

    # check for new explist data? should it be able to be updated on the fly?
