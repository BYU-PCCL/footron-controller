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
last_commercial_time = dt.now()


def should_advance(start_time):
    current_exp = api.current()

    if not current_exp:
        return True

    if current_exp.lock:
        return False

    current_date = dt.now()
    if current_exp.end_time:
        if current_date < dt.fromtimestamp(current_exp.end_time):
            return False
    elif start_time and (current_date - start_time).seconds < current_exp.lifetime:
        return False

    return True


def advance():
    global last_commercial_time
    if (
        len(api.commercials)
        and (dt.now() - last_commercial_time).seconds >= COMMERCIAL_TIMEOUT
    ):
        next = api.commercials.pop()
        last_commercial_time = dt.now()
    else:
        next = api.experiences.pop()
    api.set_current(next)

# print(commercial_base)
# TODO be able to display what's up next
while True:
    if should_advance(api._current_start):
        advance()
    time.sleep(1)
