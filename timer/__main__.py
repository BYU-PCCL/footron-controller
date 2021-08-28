from datetime import datetime as dt
import time
from .api import TimerApi 
import os


CONTROLLER_URL = (
    os.environ["FT_CONTROLLER_URL"]
    if "FT_CONTROLLER_URL" in os.environ
    else "http://localhost:8000"
)

COMMERCIAL_TIMEOUT = 15

api = TimerApi(CONTROLLER_URL)

def should_advance(start_time):
    current_exp = api.current()
    if not current_exp:
        return True
    # print("current time", flush=True)
    # print(dt.now())
    # print("endtime")
    # if current_exp.end_time: 
    #     print(dt.fromtimestamp(current_exp.end_time), flush=True)

    if current_exp.lock:
        return False
    current_date = dt.now()
    if current_exp.end_time:
        if current_date < dt.fromtimestamp(current_exp.end_time):
            return False   
    elif start_time and (current_date - start_time).seconds < current_exp.lifetime:
        return False
    # print("current_date - start_time")
    # print(current_date.timestamp() - start_time)
    # print(str.format(current_date - start_time))

    # print("should advance returned True")

    return True

commercial_timer = dt.now()

def advance():
    if api.current != api.last():
        return
    if len(api.commercials) and (dt.now() - commercial_timer).seconds >= COMMERCIAL_TIMEOUT:
        next = api.commercials.pop()
    else:
        next = api.experiences.pop()
    api.set_current(next)

# print(commercial_base)
# TODO be able to display what's up next
while True:
    if should_advance(api._current_start):
        advance()
    time.sleep(1)
