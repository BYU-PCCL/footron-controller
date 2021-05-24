import flask
from flask import request

from .apps import BaseApp
from .controller import Controller

flask_app = flask.Flask(__name__)
flask_app.config["DEBUG"] = True

controller = Controller()


def app_response(app: BaseApp):
    return {
        "id": app.id,
        "title": app.title,
        "artist": app.artist,
        "description": app.description,
    }


# Route for the home page
@flask_app.route("/", methods=["GET"])
def home():
    return "<h1>CS TV Controller</h1><p>This is the site for the CS TV API</p>"


# Route for loading apps
@flask_app.route("/reload", methods=["GET"])
def api_reload():
    controller.load_apps()
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


@flask_app.route("/current-app", methods=["GET", "PUT"])
def api_current_app():
    # TODO: Break this up into a lot of pieces

    if request.method == "GET":
        if not controller.current_app:
            return {}

        return app_response(controller.current_app)
    elif request.method == "PUT":
        body = request.json
        if body is None:
            return {"error": "No request body provided"}, 400
        if "id" not in body:
            return {"error": "'id' not found in request body"}, 400

        id = body["id"]
        if id not in controller.apps:
            return {"error": f"App with id '{id}' not registered"}, 400

        controller.set_app(id)
        return {"status": "ok"}


flask_app.run()
