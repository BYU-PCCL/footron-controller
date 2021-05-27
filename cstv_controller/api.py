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
        "lifetime": app.lifetime,
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


@flask_app.route("/current-app", methods=["GET", "PUT", "PATCH"])
def api_current_app():
    # TODO: Break this up into a lot of pieces

    if request.method == "GET":
        if not controller.current_app:
            return {}
        current_app = controller.current_app

        response_data = app_response(current_app)
        if current_app.end_time is not None:
            response_data["end_time"] = current_app.end_time

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
            if "end_time" not in body:
                return {"error": "PATCH on /current-app is only supported for end_time"}, 400

            print(body)
            end_time = body["end_time"]
            if end_time is not None and not isinstance(end_time, int):
                return {"error": "end_time must be either an integer or null"}, 400

            controller.current_app.end_time = end_time
            print(controller.current_app)

        return {"status": "ok"}


flask_app.run()
