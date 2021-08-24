import asyncio
import atexit
import dataclasses
from typing import Optional, Union

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .placard import PlacardData
from .experiences import BaseExperience
from .collection import Collection
from .controller import Controller

fastapi_app = FastAPI()

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_controller: Controller


class SetCurrentExperienceBody(BaseModel):
    id: str


class UpdateCurrentExperienceBody(BaseModel):
    id: Optional[str]
    end_time: Optional[int]
    lock: Optional[Union[int, bool]]


def experience_response(experience: BaseExperience):
    data = {
        "id": experience.id,
        "title": experience.title,
        "artist": experience.artist,
        "description": experience.description,
        "lifetime": experience.lifetime,
        "last_update": int(_controller.last_update.timestamp()),
        # TODO: Remove these dummy values once we get the API injecting them
        "thumbnails": {
            "wide": "https://via.placeholder.com/1280x800",
            "thumb": "https://via.placeholder.com/800x800",
        },
        "colors": {
            "primary": "#212121",
            "secondaryLight": "#fafafa",
            "secondaryDark": "#252525",
        },
    }

    if experience.collection:
        data["collection"] = experience.collection

    return data


def collection_response(collection: Collection):
    return dataclasses.asdict(collection)


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


@fastapi_app.get("/experiences/<id>")
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


@fastapi_app.get("/collections/<id>")
def collection(id):
    if id not in _controller.collections:
        return {}

    return collection_response(_controller.collections[id])


@fastapi_app.get("/current")
def current_experience():
    if not _controller.current_experience:
        return {}
    current = _controller.current_experience

    response_data = experience_response(current)
    if _controller.end_time is not None:
        response_data["end_time"] = _controller.end_time
    response_data["lock"] = _controller.lock

    return response_data


@fastapi_app.put("/current")
async def set_current_experience(body: SetCurrentExperienceBody):
    if body.id not in _controller.experiences:
        raise HTTPException(
            status_code=400, detail=f"Experience with id '{body.id}' not registered"
        )

    await _controller.set_experience(body.id)
    return {"status": "ok"}


@fastapi_app.patch("/current")
def update_current_experience(body: UpdateCurrentExperienceBody):
    if not _controller.current_experience:
        raise HTTPException(status_code=400, detail="No current experience exists")

    # Requiring an ID is a little bit of a hacky way to prevent an experience that
    # is transitioning out from setting properties on the incoming experience. This
    # of course assumes no foul play on the part of the experience, which shouldn't
    # be a concern for now because all experiences are manually reviewed.
    if body.id and body.id != _controller.current_experience.id:
        raise HTTPException(
            status_code=400, detail="`id` specified is not current experience"
        )

    if body.end_time:
        _controller.end_time = body.end_time
    if body.lock is not None:
        _controller.lock = body.lock

    return {"status": "ok"}


@fastapi_app.get("/placard")
async def placard():
    return await _controller.placard.get()


@fastapi_app.patch("/placard")
async def update_placard(body: PlacardData):
    return await _controller.placard.update(body)


@fastapi_app.on_event("startup")
def on_startup():
    global _controller
    _controller = Controller()


@atexit.register
def on_shutdown():
    # TODO: Handle closing in the middle of a transition (keep track of all running
    #  experiences in a dict or something)

    # Docker containers won't clean themselves up for example
    if _controller.current_experience is not None:
        if asyncio.iscoroutinefunction(_controller.current_experience.stop):
            loop = asyncio.get_event_loop()
            stop_task = loop.create_task(_controller.current_experience.stop())
            loop.run_until_complete(stop_task)
        else:
            _controller.current_experience.stop()
