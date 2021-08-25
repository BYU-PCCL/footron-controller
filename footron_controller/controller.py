import datetime
from typing import Dict, Optional
import footron_protocol as protocol

from .experiences import load_experiences_fs, BaseExperience
from .data.wm import WmApi
from .data.placard import PlacardApi, PlacardExperienceData
from .data.collection import load_collections_from_fs, Collection


class Controller:
    experiences: Dict[str, BaseExperience] = {}
    collections: Dict[str, Collection] = {}
    current_experience: Optional[BaseExperience]
    end_time: Optional[int]
    lock: protocol.Lock
    last_update: datetime.datetime
    placard: PlacardApi

    def __init__(self):
        self.current_experience = None
        self.end_time = None
        self.lock = False

        self.placard = PlacardApi()
        self.wm = WmApi()

        self.load_from_fs()

    def load_from_fs(self):
        self.load_experiences()
        self.load_collections()
        self.last_update = datetime.datetime.now()

    def load_experiences(self):
        self.experiences = {
            experience.id: experience for experience in load_experiences_fs()
        }

    def load_collections(self):
        self.collections = {
            collection.id: collection for collection in load_collections_from_fs()
        }

    async def set_experience(self, id: str):
        if self.current_experience and self.current_experience.id == id:
            return

        # Unchecked exception, consumer's responsibility to know that experience with
        # ID exists
        experience = self.experiences[id]
        await self._update_placard(experience)
        self.wm.set_fullscreen(experience.fullscreen)

        try:
            if self.current_experience:
                await self.current_experience.stop()
        finally:
            try:
                await experience.start()
            finally:
                # Environment start() and stop() methods should have their own error
                # handling, but if something is unhandled we need keep our state
                # maintained
                self.end_time = None
                self.current_experience = experience

    async def _update_placard(self, experience: BaseExperience):
        # TODO: Validate this worked somehow
        await self.placard.set_experience(
            # We include the artist even if it is none because we need a complete PATCH
            PlacardExperienceData(
                title=experience.title,
                description=experience.description,
                artist=experience.artist,
            )
        )
        await self.placard.set_visibility(not experience.fullscreen)
