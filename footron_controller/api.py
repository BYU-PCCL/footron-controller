import asyncio
import atexit
import dataclasses
import logging
from typing import Optional

import rollbar
from rollbar.contrib.fastapi import add_to as rollbar_add_to
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import footron_protocol as protocol
from .util import datetime_to_timestamp, timestamp_to_datetime
from .constants import (
    ROLLBAR_TOKEN,
    LOG_IGNORE_PATTERNS,
)
from .data.placard import PlacardExperienceData, PlacardUrlData
from .experiences import BaseExperience, VideoExperience
from .data.groupings import Collection, Folder, Tag
from .data.screenshot import create_screenshot_bytes_generator, SCREENSHOT_MIME_TYPES
from .controller import Controller

fastapi_app = FastAPI()

if ROLLBAR_TOKEN:
    rollbar.init(
        ROLLBAR_TOKEN,
        environment="production",
        handler="async",
        include_request_body=True,
    )
    rollbar_add_to(fastapi_app)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_controller: Controller


class SetCurrentExperienceBody(BaseModel):
    id: Optional[str]


class UpdateCurrentExperienceBody(BaseModel):
    id: Optional[str]
    end_time: Optional[int]
    last_interaction: Optional[int]
    lock: Optional[protocol.Lock]


# TODO: Find a cleaner way to do this
def experience_response(experience: BaseExperience):
    data = {
        "id": experience.id,
        "title": experience.title,
        "artist": experience.artist,
        "description": experience.description,
        "lifetime": experience.lifetime,
        "last_update": datetime_to_timestamp(_controller.last_update),
        "unlisted": experience.unlisted,
        "queueable": experience.queueable,
        "folders": _controller.experience_folders_map[experience.id],
        "tags": _controller.experience_tag_map[experience.id],
    }

    if experience.id in _controller.experience_collection_map.keys():
        data["collection"] = _controller.experience_collection_map[experience.id]

    if isinstance(experience, VideoExperience):
        data["scrubbing"] = experience.scrubbing

    return data


def collection_response(collection: Collection):
    return collection.dict()


def folder_response(folder: Folder):
    return folder.dict()


def tag_response(tag: Tag):
    return tag.dict()


# Route for reloading data
@fastapi_app.get("/reload")
def api_reload():
    _controller.load_from_fs()
    return {"status": "ok"}


# TODO: Finish
@fastapi_app.get("/experiences")
def experiences():
    return {
        id: experience_response(experience)
        for id, experience in _controller.experiences.items()
    }


@fastapi_app.get("/experiences/{id}")
def experience(id):
    if id not in _controller.experiences:
        return {}

    return experience_response(_controller.experiences[id])


@fastapi_app.get("/collections")
def collections():
    return {
        id: collection_response(collection)
        for id, collection in _controller.collections.items()
    }


@fastapi_app.get("/collections/{id}")
def collection(id):
    if id not in _controller.collections:
        return {}

    return collection_response(_controller.collections[id])


@fastapi_app.get("/folders")
def folders():
    return {
        id: folder_response(folder)
        for id, folder in _controller.folders.items()
        if folder.visible
    }


@fastapi_app.get("/folders/{id}")
def folder(id):
    if id not in _controller.folders:
        return {}

    return folder_response(_controller.folders[id])


@fastapi_app.get("/tags")
def tags():
    return {id: tag_response(tag) for id, tag in _controller.tags.items()}


@fastapi_app.get("/tags/{id}")
def tag(id):
    if id not in _controller.tags:
        return {}

    return tag_response(_controller.tags[id])


@fastapi_app.get("/current")
async def current_experience():
    if not _controller.current:
        return {}
    current = _controller.current

    response_data = experience_response(current.experience)
    if current.end_time is not None:
        response_data["end_time"] = datetime_to_timestamp(current.end_time)
    if current.start_time is not None:
        response_data["start_time"] = datetime_to_timestamp(current.start_time)
    if _controller.lock.last_update is not None:
        response_data["last_lock_update"] = datetime_to_timestamp(
            _controller.lock.last_update
        )
    if current.last_interaction is not None:
        response_data["last_interaction"] = datetime_to_timestamp(
            current.last_interaction
        )
    response_data["lock"] = _controller.lock.status

    return response_data


@fastapi_app.put("/current")
async def set_current_experience(
    body: SetCurrentExperienceBody, throttle: Optional[int] = None
):
    if body.id is not None and body.id not in _controller.experiences:
        raise HTTPException(
            status_code=400, detail=f"Experience with id '{body.id}' not registered"
        )

    if not await _controller.set_experience(body.id, throttle=throttle):
        throttle_scenario = "while it was changing"
        if throttle:
            throttle_scenario = (
                "either {throttle_scenario} or before timeout "
                "specified in 'throttle' parameter"
            )
        raise HTTPException(
            status_code=429,
            detail=f"Tried to change current experience {throttle_scenario}",
        )

    return {"status": "ok"}


@fastapi_app.patch("/current")
async def update_current_experience(body: UpdateCurrentExperienceBody):
    if not _controller.current:
        raise HTTPException(status_code=400, detail="No current experience exists")

    # Requiring an ID is a little bit of a hacky way to prevent an experience that
    # is transitioning out from setting properties on the incoming experience. This
    # of course assumes no foul play on the part of the experience, which shouldn't
    # be a concern for now because all experiences are manually reviewed.
    if body.id and body.id != _controller.current.id:
        raise HTTPException(
            status_code=400, detail="`id` specified is not current experience"
        )

    if body.end_time:
        _controller.current.end_time = timestamp_to_datetime(body.end_time)
    if body.last_interaction:
        _controller.current.last_interaction = timestamp_to_datetime(
            body.last_interaction
        )
    if body.lock is not None:
        _controller.lock = body.lock

    return {"status": "ok"}


@fastapi_app.get("/placard/experience")
async def placard_experience():
    return await _controller.placard.experience()


@fastapi_app.patch("/placard/experience")
async def update_placard_experience(body: PlacardExperienceData):
    return await _controller.placard.set_experience(body)


@fastapi_app.get("/placard/url")
async def placard_url():
    if not (placard := _controller.placard):
        return {"url": None}
    return await placard.url()


@fastapi_app.patch("/placard/url")
async def update_placard_url(body: PlacardUrlData):
    if not (placard := _controller.placard):
        # Just fail silently if there's no placard
        return {"status": "no_placard"}
    return await _controller.placard.set_url(body.url)


@fastapi_app.get("/screenshot")
async def screenshot(
    w: Optional[int] = None, h: Optional[int] = None, format: str = "jpeg", q: int = 95
):
    format = format.lower()
    if format not in SCREENSHOT_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"'format' parameter has invalid value '{format}'",
        )

    return StreamingResponse(
        create_screenshot_bytes_generator(width=w, height=h, quality=q, format=format),
        media_type=SCREENSHOT_MIME_TYPES[format],
    )


@fastapi_app.on_event("startup")
def on_startup():
    global _controller
    _controller = Controller()
    asyncio.get_event_loop().create_task(_controller.stability_loop())
    asyncio.get_event_loop().create_task(_controller.handle_experience_exit_loop())


@atexit.register
def on_shutdown():
    # TODO: Handle closing in the middle of a transition (keep track of all running
    #  experiences in a dict or something)

    # Docker containers won't clean themselves up for example
    if _controller.current is not None:
        if asyncio.iscoroutinefunction(_controller.current.stop):
            loop = asyncio.get_event_loop()
            stop_task = loop.create_task(_controller.current.stop())
            loop.run_until_complete(stop_task)
        else:
            _controller.current.stop()


# See https://github.com/encode/starlette/issues/864#issuecomment-653076434
class PolledEndpointsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno > logging.INFO:
            return True

        message = record.getMessage()

        if any(filter(lambda a: a.search(message), LOG_IGNORE_PATTERNS)):
            return False

        return True


# Filter out especially verbose endpoints
logging.getLogger("uvicorn.access").addFilter(PolledEndpointsFilter())
