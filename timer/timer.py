import datetime
import random
import time

# from apscheduler.schedulers.background import BackgroundScheduler

# Also gotta see what apps are actually able to be used (cameras online?)
app_list = {
    "app_list": [
        {
            "name" : "life",
            "lifetime" : 30,
        },
        {
            "name" : "smoke",
            "lifetime" : 45,
        },
        {
            "name" : "hair",
            "lifetime" : 27,
        },
    ]

}
# read in json


# shuffle list
def shuffle_list(ls):
    playlist = []
    for x in ls :
        playlist.append({})

    print(playlist)

    list_length = len(ls)
    for x in ls :
        addAt = random.randint(0, list_length-1)
        while True:
            if playlist[addAt] == {}:
                playlist[addAt] = x
                # print("added " + x["name"] + " at " + str(addAt))
                break
            else:
                # print(addAt)
                # print(playlist[addAt])
                addAt += 1
                if addAt > (list_length - 1):
                    addAt -= list_length
        
    print(playlist)

    return playlist


# set up scheduler
# scheduler = BackgroundScheduler()
# scheduler.start()


# send commands to controller

cont = True

while cont:
    playlist = shuffle_list(app_list["app_list"])
    for app in playlist:
        
        
        # scheduler.add_job(lambda : scheduler.print_jobs(), 'interval', minutes=app["lifetime"])
        
        # scheduler.add_job(lambda : print(app["name"]), 'interval', minutes=app["lifetime"])
        print(app["name"])

        # wait for confirmation that it's running?
        start_time = datetime.datetime.now()
        while ((datetime.datetime.now() - start_time).total_seconds() < app["lifetime"]):
            time.sleep(10)
            print("10 SECONDS HAVE PASSED")

    # check for new app_list data? should it be able to be updated on the fly?

# do forever
    # while list isn't empty 
        # send id 
        # wait for amount of time
        # follow list
    # reshuffle after list empty 