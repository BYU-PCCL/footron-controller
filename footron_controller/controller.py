import asyncio
import datetime
from typing import Dict, Optional

from .experiences import load_experiences_fs, BaseExperience
from .placard import PlacardApi, PlacardData
from .collection import load_collections_from_fs, Collection


class Controller:
    experiences: Dict[str, BaseExperience] = {}
    collections: Dict[str, Collection] = {}
    current_experience: Optional[BaseExperience]
    end_time: Optional[int]
    last_update: datetime.datetime
    placard: PlacardApi

    def __init__(self):
        self.current_experience = None
        self.end_time = None

        self.placard = PlacardApi()

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

        try:
            await experience.start()
            if self.current_experience:
                # Wait for first experience to fade out so transition is seamless
                await asyncio.sleep(0.5)
                await self.current_experience.stop()
        finally:
            # Environment start() and stop() methods should have their own error
            # handling, but if something is unhandled we need keep our state maintained
            self.end_time = None
            self.current_experience = experience

    async def _update_placard(self, experience: BaseExperience):
        # TODO: Validate this worked somehow
        await self.placard.update(
            # We include the artist even if it is none because we need a complete PATCH
            PlacardData(
                title=experience.title,
                description=experience.description,
                artist=experience.artist,
            )
        )
