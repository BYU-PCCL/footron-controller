import asyncio
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp.client_exceptions
import rollbar

from .constants import (
    BASE_BIN_PATH,
    DISABLE_PLACARD,
    DISABLE_WM,
    EMPTY_EXPERIENCE_DATA,
    EXPERIENCE_DATA_PATH,
    EXPERIENCES_PATH,
    INITIAL_EMPTY_EXPERIENCE_DELAY_S,
    STABILITY_CHECK,
)
from .data.colors import ColorManager
from .data.groupings import Collection, Folder, Tag, load_experience_grouping
from .data.loader import LoaderManager
from .data.placard import PlacardApi, PlacardExperienceData
from .data.screenshot import ScreenshotCapture
from .data.stability import StabilityManager
from .data.wm import DisplayLayout, WmApi
from .environments import EnvironmentState
from .experiences import (
    BaseExperience,
    CurrentExperience,
    DockerExperience,
    load_experiences_fs,
)

logger = logging.getLogger(__name__)


class Controller:
    # TODO: Redo these hints the way FastAPI does them internally
    experiences: Dict[str, BaseExperience]
    # TODO: Think up a cleaner way to do this...
    collections: Dict[str, Collection]
    tags: Dict[str, Tag]
    folders: Dict[str, Folder]
    colors: ColorManager
    # TODO: ...and this
    experience_collection_map: Dict[str, str]
    experience_tags_map: Dict[str, List[str]]
    last_update: datetime
    last_started_setting_experience: Optional[datetime]
    _wm: Optional[WmApi]
    _screenshot_capture: ScreenshotCapture
    _placard: Optional[PlacardApi]
    _stability: StabilityManager
    _loader: LoaderManager
    _current: Optional[CurrentExperience]
    _modify_lock: asyncio.Lock

    def __init__(self):
        self._modify_lock = asyncio.Lock()

        self.experiences = {}
        self.collections = {}
        self.tags = {}
        self.experience_collection_map = {}
        self.experience_tags_map = {}
        self.last_started_setting_experience = None

        self._screenshot_capture = ScreenshotCapture()
        self._wm = WmApi() if not DISABLE_WM else None
        self._placard = PlacardApi() if not DISABLE_PLACARD else None
        self._stability = StabilityManager()
        self._loader = LoaderManager(self._wm)
        self._current = None

        self._create_paths()
        self.load_from_fs()
        # Clear the placard when starting up, but not if an experience has already been
        # set within the last 5 seconds--this should fix our problem with placard races
        # when starting up
        asyncio.get_event_loop().create_task(self._set_initial_empty_experience())

    def load_from_fs(self):
        self.load_experiences()
        self.load_collections()
        self.load_tags()
        self.load_folders()
        self.load_colors()
        self.last_update = datetime.now()

    def load_experiences(self):
        self.experiences = {
            experience.id: experience for experience in load_experiences_fs()
        }

    def load_collections(self):
        self.collections = load_experience_grouping(Collection, "collections.toml")
        self._fill_experience_collection_map()

    def load_folders(self):
        self.folders = load_experience_grouping(Folder, "folders.toml")
        self._fill_experience_folder_map()

    def load_tags(self):
        self.tags = load_experience_grouping(Tag, "tags.toml")
        self._fill_experience_tag_map()

    def load_colors(self):
        self.colors = ColorManager()
        self.colors.load(list(self.experiences.values()))

    @property
    def current(self) -> Optional[CurrentExperience]:
        return self._current

    @property
    def screenshot_capture(self):
        return self._screenshot_capture

    @property
    def placard(self):
        return self._placard

    @property
    def lock(self):
        return self._current.lock

    @lock.setter
    def lock(self, value):
        asyncio.get_event_loop().create_task(self._set_lock_impl(value))

    async def _set_lock_impl(self, value):
        async with self._modify_lock:
            self._current.lock = value

    def _fill_experience_collection_map(self):
        self.experience_collection_map = {}
        for collection in self.collections.values():
            for experience in collection.experiences:
                self.experience_collection_map[experience] = collection.id

    def _fill_experience_tag_map(self):
        self.experience_tag_map = {}
        for experience in self.experiences:
            self.experience_tag_map[experience] = []
        for tag in self.tags.values():
            for experience in tag.experiences:
                if experience not in self.experience_tag_map:
                    continue

                self.experience_tag_map[experience].append(tag.id)

    def _fill_experience_folder_map(self):
        self.experience_folders_map = {}
        for experience in self.experiences:
            self.experience_folders_map[experience] = []

        for folder in self.folders.values():
            for tag in folder.tags:
                for experience in self.tags[tag].experiences:
                    if experience not in self.experiences:
                        continue
                    self.experience_folders_map[experience].append(folder.id)

    @staticmethod
    def _create_paths():
        EXPERIENCES_PATH.mkdir(parents=True, exist_ok=True)
        EXPERIENCE_DATA_PATH.mkdir(parents=True, exist_ok=True)
        BASE_BIN_PATH.mkdir(parents=True, exist_ok=True)

    async def _update_experience_display(self, experience: Optional[BaseExperience]):
        await self._try_launch_loader(experience)
        # We don't actually want to wait for this to complete
        if self._placard:
            asyncio.get_event_loop().create_task(self._update_placard(experience))
        if self._wm:
            await self._wm.set_layout(
                experience.layout if experience else DisplayLayout.Wide
            )

    async def set_experience(
        self, id: Optional[str], *, throttle: int = None, update_throttle: bool = True
    ) -> bool:
        delta_last_experience = (
            (datetime.now() - self.last_started_setting_experience)
            if throttle and self._current and self.last_started_setting_experience
            else None
        )

        if (
            delta_last_experience
            and delta_last_experience.seconds < throttle
            and delta_last_experience.days == 0
        ):
            return False

        # We just return here instead of waiting for a lock because we don't want
        # experience changes to queue up and lock up the display.
        if self._modify_lock.locked():
            return False

        async with self._modify_lock:
            await self._set_experience_impl(id, update_throttle=update_throttle)
        return True

    async def _set_experience_impl(
        self, id: Optional[str], *, update_throttle: bool = True
    ):
        if self._current and self._current.id == id:
            return

        if update_throttle:
            self.last_started_setting_experience = datetime.now()

        # Unchecked exception, consumer's responsibility to know that experience with
        # ID exists
        experience = self.experiences[id] if id else None
        await self._update_experience_display(experience)

        try:
            if self._wm:
                await self._wm.clear_viewport()
            if self._current:
                asyncio.get_event_loop().create_task(self._current.stop(experience))
        finally:
            try:
                if experience:
                    if experience.load_time:
                        # Wait for loading screen to kick in (we need a better solution
                        # here)
                        await asyncio.sleep(1)
                    await experience.start(
                        self._current.experience if self._current else None
                    )
            except Exception:
                self._current = None
                raise
            else:
                self._current = (
                    CurrentExperience(experience, datetime.now())
                    if experience
                    else None
                )

    async def _set_initial_empty_experience(self):
        await asyncio.sleep(INITIAL_EMPTY_EXPERIENCE_DELAY_S)
        await self.set_experience(
            None,
            throttle=INITIAL_EMPTY_EXPERIENCE_DELAY_S,
            update_throttle=False,
        )

    async def _try_launch_loader(self, experience: BaseExperience):
        if not experience or not experience.load_time:
            return

        await self._loader.start()
        asyncio.get_event_loop().create_task(
            self._loader.stop_after_timeout(experience.load_time)
        )

    async def _update_placard(self, experience: BaseExperience):
        # TODO: Validate this worked somehow
        try:
            # We don't switch the name on a fullscreen experience because it makes an
            # ugly flash
            if not experience or experience.layout != DisplayLayout.Full:
                await self._placard.set_experience(
                    PlacardExperienceData(
                        title=experience.title,
                        description=experience.long_description
                        if experience.long_description
                        else experience.description,
                        artist=experience.artist,
                    )
                    if experience
                    else EMPTY_EXPERIENCE_DATA
                )
            await self._placard.set_layout(
                PlacardApi.placard_layout_from_display_layout(
                    experience.layout if experience else DisplayLayout.Wide
                )
            )
            await self._placard.set_action_hints(
                experience.action_hints if experience else []
            )
        except aiohttp.client_exceptions.ClientError:
            logger.warning(
                "Updating placard failed with client exception, retrying in 1s"
            )
            # Wait for a second and try again
            await asyncio.sleep(1)
            await self._update_placard(experience)

    async def _cleanup_rogue_docker_containers(self):
        for experience in self.experiences.values():
            if not isinstance(experience, DockerExperience) or (
                self._current and experience.id == self._current.id
            ):
                continue
            await experience.attempt_cleanup()

    async def colors_handling_loop(self):
        while True:
            try:
                self.colors.load_queued_colors()
            except Exception as e:
                rollbar.report_exc_info(e)
                logger.exception("Error while handling colors")
            await asyncio.sleep(1)

    async def handle_experience_exit_loop(self):
        while True:
            logger.debug("Checking current experience state for exit...")
            try:
                if (
                    self._current
                    and (await self._current.environment.state())
                    == EnvironmentState.FAILED
                ):
                    logger.error(
                        "Environment failed, attempting to set current experience to empty..."
                    )
                    await self.set_experience(None, throttle=5)
            except Exception as e:
                rollbar.report_exc_info(e)
                logger.exception("Error while handling experience exit loop")
            await asyncio.sleep(1)

    async def stability_loop(self):
        # TODO: Break this method up
        while True:
            logging.debug("Checking system stability...")
            try:
                asyncio.get_event_loop().create_task(
                    self._cleanup_rogue_docker_containers()
                )

                if STABILITY_CHECK and not self._stability.check_stable():
                    rollbar.report_message("System is unstable, rebooting")
                    logging.error("System is unstable, rebooting")
                    # Note that the current user has to have NOPASSWD set up in
                    # /etc/sudoers for /sbin/reboot on Ubuntu systems for this to
                    # work from Python
                    os.system("sudo reboot")
            except Exception as e:
                rollbar.report_exc_info(e)
                logger.exception("Error while checking stability")
            await asyncio.sleep(15)
