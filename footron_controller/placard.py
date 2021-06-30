import os
import urllib.parse

import requests_unixsocket

_PLACARD_SOCKETS_PATH = os.path.join(os.environ["XDG_RUNTIME_DIR"], "placard", "socket")


class PlacardApi:
    def __init__(self):
        self._domain_sockets_session = requests_unixsocket.Session()
        self._placard_escaped_url = (
            f"http+unix://{urllib.parse.quote_plus(_PLACARD_SOCKETS_PATH)}"
        )

    def update(self, data):
        return self._domain_sockets_session.patch(
            f"{self._placard_escaped_url}/placard", json=data
        ).json()

    def get(self):
        return self._domain_sockets_session.get(
            f"{self._placard_escaped_url}/placard"
        ).json()
