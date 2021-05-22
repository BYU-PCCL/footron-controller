import random
import time

# Also gotta see what apps are actually able to be used (cameras online?)
app_list = {
    "app_list": [
        {
            "name" : "life",
            "lifetime" : 60,
        },
        {
            "name" : "smoke",
            "lifetime" : 59,
        },
        {
            "name" : "hair",
            "lifetime" : 70,
        },
    ]

}
# read in json


# shuffle list
def shuffle_list(ls):
    playlist = []
    for x in ls :
        playlist.append[{}]

    list_length = ls.count()
    for list_length in ls :
        addAt = random.randint(0, list_length-1)
        while true:
            if playlist[addAt] == {}:
                playlist[addAt] = x
                break
            else:
                addAt += 1
                if addAt > (list_length - 1):
                    addAt -= list_length
        
    return playlist




# send commands to controller

cont = true

while cont:
    playlist = shuffle_list(app_list["app_list"])
    for app in playlist:
        print(app[0]["name"])
        # wait for confirmation that it's running?
        time.sleep(app[0]["lifetime"])
    # check for new app_list data? should it be able to be updated on the fly?

# do forever
    # while list isn't empty 
        # send id 
        # wait for amount of time
        # follow list
    # reshuffle after list empty 