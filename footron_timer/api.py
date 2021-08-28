from datetime import datetime as dt
from .models import Experience, CurrentExperience
import random
import requests
from typing import List
import urllib.parse


EXPERIENCES_ENDPOINT = "experiences"
CURRENT_ENDPOINT = "current"


class TimerApi:
    def __init__(self, url) -> None:
        self._url = url
        self._experiences_endpoint = urllib.parse.urljoin(
            self._url, EXPERIENCES_ENDPOINT
        )
        self._current_endpoint = urllib.parse.urljoin(self._url, CURRENT_ENDPOINT)
        self._current = None
        self._last = None
        self._current_start = None
        self.reload()

    def current(self):
        exp_data = requests.get(self._current_endpoint).json()
        if not exp_data:
            self._current = None
            return self._current
        self._current = CurrentExperience.parse_obj(exp_data)
        return self._current

    def last(self):
        return self._last

    def reload(self):
        explist: List[Experience] = list(
            map(
                Experience.parse_obj,
                requests.get(self._experiences_endpoint).json().values(),
            )
        )
        commercial_base = []
        exp_base = []
        collection_base = {}
        for exp in explist:
            if exp.collection:
                collection = exp.collection
                if collection == "commercials":
                    commercial_base.append(exp)
                else:
                    if collection not in collection_base:
                        collection_base[collection] = []
                    collection_base[collection].append(exp)
            else:
                if exp.unlisted:
                    continue
                exp_base.append(exp)

        for collection in collection_base.values():
            exp_base.append(Playlist(collection))

        self.experiences = Playlist(exp_base)
        self.commercials = Playlist(commercial_base)

    def set_current(self, current):
        # TODO check HTTP code before updating internal state
        requests.put(
            self._current_endpoint,
            headers={"Content-Type": "application/json"},
            json={"id": current.id},
        )
        self._last = self._current
        self._current = current
        self._current_start = dt.now()


class Playlist:
    def __init__(self, source) -> None:
        self._source = source
        self.reload()

    def __len__(self):
        return len(self._source)

    def pop(self):
        if not self._shuffled:
            self.reload()
        item = self._shuffled.pop()
        if isinstance(item, Playlist):
            return item.pop()
        return item

    def reload(self):
        self._shuffled = self._source.copy()
        random.shuffle(self._shuffled)
