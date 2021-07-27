import asyncio
import atexit
import dataclasses
import hashlib
import tarfile
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .releases import ReleaseManager
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

_releases: ReleaseManager
_controller: Controller


class SetCurrentExperienceBody(BaseModel):
    id: str


class UpdateCurrentExperienceBody(BaseModel):
    id: str
    end_time: Optional[int]


class SetExperienceReleaseBody(BaseModel):
    hash: Optional[str]


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
    if body.id != _controller.current_experience.id:
        raise HTTPException(
            status_code=400, detail="`id` specified is not current experience"
        )

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
    global _releases, _controller
    _releases = ReleaseManager()
    _controller = Controller(_releases)


@fastapi_app.get("/releases")
def releases():
    return _releases.data


@fastapi_app.post("/releases/{id}")
async def add_release(id: str, file: UploadFile = File(...)):
    # TODO: Is this too slow? Will it freeze the controller?
    uncompressed_file = tarfile.open(fileobj=file.file, mode="r:gz")
    tar_fileobj = uncompressed_file.fileobj

    # TODO: This might not work for comparing contents, we need to do something like
    #  https://gist.github.com/DaveCTurner/8765561 MAKING SURE THAT WE COMPARE FILE
    #  PERMISSIONS (see https://docs.python.org/3/library/tarfile.html#tarinfo-objects
    #  for a lead on where to get file metadata)
    hash = hashlib.sha256()
    while True:
        chunk = tar_fileobj.read(4096)
        if not chunk:
            break
        hash.update(chunk)

    # Produces a hash different than sha256sum on the same file locally--this might not
    # be a problem but we should be aware that it could be. Might be an encoding thing,
    # not sure.
    hash = bytes.hex(hash.digest())

    if _releases.release_exists(id, hash):
        return HTTPException(
            status_code=400, detail=f"This release already exists with hash '{hash}'"
        )

    uncompressed_file.extractall(_releases.create_release(id, hash))

    return {"hash": hash}


@fastapi_app.put("/releases/{id}")
async def set_release(id: str, body: SetExperienceReleaseBody):
    if body.hash:
        _releases.set_release(id, body.hash)
    else:
        _releases.reset_release(id)
    _controller.load_from_fs()
    return {"status": "ok"}


@atexit.register
def cleanup():
    # TODO: Handle closing in the middle of a transition (keep track of all running
    #  experiences in a dict or something)

    # Docker containers won't clean themselves up for example
    if _controller.current_experience is not None:
        loop = asyncio.get_event_loop()
        stop_task = loop.create_task(_controller.current_experience.stop())
        loop.run_until_complete(stop_task)
