import os
import urllib.parse
from time import sleep
from typing import Dict, Optional

import requests_unixsocket

from .apps import BaseApp, load_apps_from_fs

_PLACARD_SOCKETS_PATH = os.path.join(os.environ["XDG_RUNTIME_DIR"], "placard", "socket")


class Controller:
    apps: Dict[str, BaseApp] = {}
    current_app: Optional[BaseApp]
    end_time: Optional[int]

    def __init__(self):
        self._domain_sockets_session = requests_unixsocket.Session()
        self._placard_escaped_url = (
            f"http+unix://{urllib.parse.quote_plus(_PLACARD_SOCKETS_PATH)}"
        )

        self.current_app = None
        self.end_time = None
        self.load_apps()

    def load_apps(self):
        self.apps = {app.id: app for app in load_apps_from_fs()}

    def set_app(self, id: str):
        if self.current_app and self.current_app.id == id:
            return

        # Unchecked exception, consumer's responsibility to know that app with ID exists
        app = self.apps[id]
        self._update_placard(app)
        app.start()
        if self.current_app:
            # Wait for first application to fade out so transition is seamless TODO:
            #  Don't block here, though it makes sense that the response should only
            #  be sent once we know that an app was launched successfully
            sleep(0.5)
            self.current_app.stop()
        self.end_time = None
        self.current_app = app

    def _update_placard(self, app: BaseApp):
        data = {"title": app.title, "description": app.description}

        if app.artist:
            data["artist"] = app.artist

        # TODO: Validate this worked somehow
        self._domain_sockets_session.post(
            f"{self._placard_escaped_url}/content",
            json=data,
        )

        sidebar_visibility_endpoint = "show" if app.show_sidebar else "hide"
        self._domain_sockets_session.post(
            f"{self._placard_escaped_url}/{sidebar_visibility_endpoint}",
            json=data,
        )
