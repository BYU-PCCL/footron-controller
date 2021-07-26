import asyncio
import atexit
import dataclasses
from typing import Optional

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
    id: str
    end_time: Optional[int]


def experience_response(experience: BaseExperience):
    data = {
        "id": experience.id,
        "title": experience.title,
        "artist": experience.artist,
        "description": experience.description,
        "lifetime": experience.lifetime,
        "last_update": int(_controller.last_update.timestamp()),
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
    return {id: experience_response(app) for id, app in _controller.experiences.items()}


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
    current_app = _controller.current_experience

    response_data = experience_response(current_app)
    if _controller.end_time is not None:
        response_data["end_time"] = _controller.end_time

    return response_data


@fastapi_app.put("/current")
async def set_current_experience(body: SetCurrentExperienceBody):
    if body.id not in _controller.experiences:
        raise HTTPException(
            status_code=400, detail=f"App with id '{body.id}' not registered"
        )

    await _controller.set_app(body.id)
    return {"status": "ok"}


@fastapi_app.patch("/current")
def update_current_experience(body: UpdateCurrentExperienceBody):
    # Requiring an ID is a little bit of a hacky way to prevent an app that
    # is transitioning out from setting properties on the incoming app. This
    # of course assumes no foul play on the part of the app, which shouldn't
    # be a concern for now because all apps are manually reviewed.
    if body.id != _controller.current_experience.id:
        raise HTTPException(status_code=400, detail="`id` specified is not current app")

    _controller.end_time = body.end_time

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
    #  apps in a dict or something)

    # Docker containers won't clean themselves up for example
    if _controller.current_experience is not None:
        loop = asyncio.get_event_loop()
        stop_task = loop.create_task(_controller.current_experience.stop())
        loop.run_until_complete(stop_task)
