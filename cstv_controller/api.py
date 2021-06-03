import dataclasses

import flask
from flask import request

from .apps import BaseApp
from .collections import Collection
from .controller import Controller
import atexit

flask_app = flask.Flask(__name__)
flask_app.config["DEBUG"] = True

controller = Controller()


def app_response(app: BaseApp):
    data = {
        "id": app.id,
        "title": app.title,
        "artist": app.artist,
        "description": app.description,
        "lifetime": app.lifetime,
    }

    if app.collection:
        data["collection"] = app.collection

    return data


def collection_response(collection: Collection):
    return dataclasses.asdict(collection)


# Route for the home page
@flask_app.route("/", methods=["GET"])
def home():
    return "<h1>CS TV Controller</h1><p>This is the site for the CS TV API</p>"


# Route for reloading data
@flask_app.route("/reload", methods=["GET"])
def api_reload():
    controller.load_from_fs()
    return {"status": "ok"}


# Route for returning all available apps
@flask_app.route("/apps", methods=["GET"])
def api_apps():
    return {id: app_response(app) for id, app in controller.apps.items()}


@flask_app.route("/apps/<id>", methods=["GET"])
def api_app(id):
    if id not in controller.apps:
        return {}

    return app_response(controller.apps[id])


# Route for returning all available apps
@flask_app.route("/collections", methods=["GET"])
def api_collections():
    return {
        id: collection_response(collection)
        for id, collection in controller.collections.items()
    }


# Route for returning all available apps
@flask_app.route("/collections/<id>", methods=["GET"])
def api_collection(id):
    if id not in controller.collections:
        return {}

    return collection_response(controller.collections[id])


@flask_app.route("/current-app", methods=["GET", "PUT", "PATCH"])
def api_current_app():
    # TODO: Break this up into a lot of pieces

    if request.method == "GET":
        if not controller.current_app:
            return {}
        current_app = controller.current_app

        response_data = app_response(current_app)
        if controller.end_time is not None:
            response_data["end_time"] = controller.end_time

        return response_data
    elif request.method in ["PUT", "PATCH"]:
        body = request.json
        if body is None:
            return {"error": "No request body provided"}, 400

        if request.method == "PUT":
            if "id" not in body:
                return {"error": "'id' not found in request body"}, 400

            id = body["id"]
            if id not in controller.apps:
                return {"error": f"App with id '{id}' not registered"}, 400

            controller.set_app(id)
        elif request.method == "PATCH":
            # Requiring an ID is a little bit of a hacky way to prevent an app that
            # is transitioning out from setting properties on the incoming app. This
            # of course assumes no foul play on the part of the app, which shouldn't
            # be a concern for now because all apps are manually reviewed.
            if "id" not in body:
                return {"error": "id of requesting app must be specified in `id`"}, 400

            if "end_time" not in body:
                return {
                    "error": "PATCH on /current-app is only supported for `end_time`"
                }, 400

            end_time = body["end_time"]
            if end_time is not None and not isinstance(end_time, int):
                return {"error": "`end_time` must be either an integer or null"}, 400

            id = body["id"]

            if id is None or not isinstance(id, str):
                return {"error": "`id` must be a string"}, 400

            if id != controller.current_app.id:
                return {"error": "`id` specified is not current app"}, 400

            controller.end_time = end_time

        return {"status": "ok"}


@atexit.register
def cleanup():
    # TODO: Handle closing in the middle of a transition (keep track of all running
    #  apps in a dict or something)

    # Docker containers won't clean themselves up for example
    if controller.current_app is not None:
        controller.current_app.stop()


flask_app.run()
