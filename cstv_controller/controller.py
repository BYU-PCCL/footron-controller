import datetime
from time import sleep
from typing import Dict, Optional

from .placard import PlacardApi
from .apps import BaseApp, load_apps_from_fs
from .collections import load_collections_from_fs, Collection


class Controller:
    apps: Dict[str, BaseApp] = {}
    collections: Dict[str, Collection] = {}
    current_app: Optional[BaseApp]
    end_time: Optional[int]
    last_update: datetime.datetime
    placard: PlacardApi

    def __init__(self):
        self.current_app = None
        self.end_time = None

        self.placard = PlacardApi()

        self.load_from_fs()

    def load_from_fs(self):
        self.load_apps()
        self.load_collections()
        self.last_update = datetime.datetime.now()

    def load_apps(self):
        self.apps = {app.id: app for app in load_apps_from_fs()}

    def load_collections(self):
        self.collections = {
            collection.id: collection for collection in load_collections_from_fs()
        }

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
        self.placard.update(data)
