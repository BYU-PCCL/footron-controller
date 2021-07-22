import asyncio
import datetime
from typing import Dict, Optional

from .types import PlacardData
from .placard import PlacardApi
from .apps import BaseApp, load_apps_from_fs
from .collection import load_collections_from_fs, Collection


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

    async def set_app(self, id: str):
        if self.current_app and self.current_app.id == id:
            return

        # Unchecked exception, consumer's responsibility to know that app with ID exists
        app = self.apps[id]
        await self._update_placard(app)

        try:
            app.start()
            if self.current_app:
                # Wait for first application to fade out so transition is seamless
                await asyncio.sleep(0.5)
                self.current_app.stop()
        finally:
            # App start() and stop() methods should have their own error handling,
            # but if something is unhandled we need keep our state maintained
            self.end_time = None
            self.current_app = app

    async def _update_placard(self, app: BaseApp):
        # TODO: Validate this worked somehow
        await self.placard.update(
            # We include the artist even if it is none because we need a complete PATCH
            PlacardData(title=app.title, description=app.description, artist=app.artist)
        )
