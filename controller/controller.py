import shlex
import subprocess
from time import sleep

import requests_unixsocket
import flask
import os
import urllib.parse
from flask import request, jsonify

app = flask.Flask(__name__)
app.config["DEBUG"] = True

domain_sockets_session = requests_unixsocket.Session()
PLACARD_SOCKETS_PATH = os.path.join(os.environ["XDG_RUNTIME_DIR"], "placard", "socket")

service_process = None

# Test data for the CS TV, a list of dictionaries
services = {
    0: {
        "id": 0,
        "title": "Digital CSS clock",
        "description": "This digital CSS clock that we stole from someone online will only serve to demonstrate the "
        "capabilities of this very long description.",
        "artist": "Some poor developer",
        "sidebarVisible": True,
        "path": "../apps/clock/index.html",
    },
    1: {
        "id": 1,
        "title": "Yet another CSS clock",
        "description": "This CSS clock is exactly like the last one.",
        "artist": "Test test test",
        "sidebarVisible": True,
        "path": "../apps/clock2/index.html",
    },
}


# Run this to load the services from the apps directory
def load_services():
    # Decide where to put the apps directory
    # Load the dictionary file with all the services.
    print("Services being Loaded")


# Route for the home page
@app.route("/", methods=["GET"])
def home():
    return "<h1>CS TV Controller</h1><p>This is the site for the CS TV API</p>"


# Route for loading services
@app.route("/reload", methods=["GET"])
def api_reload():
    load_services()


# Route for returning all available services
@app.route("/services/all", methods=["GET"])
def api_all():
    return jsonify(services)


@app.route("/services", methods=["GET"])
def api_id():
    # TODO: Break this up into a lot of pieces
    # Check for an id in the URL.
    # If ID was provided assign it to a variable.
    # If no ID was provided display error message.
    if "id" not in request.args:
        return {"error": "id not specified"}, 400

    id = int(request.args["id"])

    if id not in services:
        return {"error": "service not found"}, 204

    service = services[id]

    path = os.path.abspath(service["path"])
    command_line = f'google-chrome --app="file://{path}" --user-data-dir=/tmp/cstv-chrome-data/{id} --no-first-run'
    args = shlex.split(command_line)

    global service_process
    last_process = service_process

    service_process = subprocess.Popen(args)

    data = {"title": service["title"], "description": service["description"]}

    if "artist" in service:
        data["artist"] = service["artist"]

    # TODO: Validate this somehow
    domain_sockets_session.post(
        f"http+unix://{urllib.parse.quote_plus(PLACARD_SOCKETS_PATH)}/content",
        json=data,
    )

    sidebar_visibility_endpoint = "show" if service["sidebarVisible"] else "hide"
    domain_sockets_session.post(
        f"http+unix://{urllib.parse.quote_plus(PLACARD_SOCKETS_PATH)}/{sidebar_visibility_endpoint}",
        json=data,
    )

    if last_process:
        # TODO: Don't block here, though it makes sense that the response should only be sent once we know that an app
        #  was launched successfully
        # Waits for first application to fade out so transition is seamless
        sleep(2)
        last_process.terminate()

    return jsonify(services[id])


load_services()
app.run()
