import flask
from flask import request, jsonify

app = flask.Flask(__name__)
app.config["DEBUG"] = True

# Test data for the CS TV, a list of dictionaries
services = {
    0: {
        'id': 0,
        'name': 'Game of life',
    },
    1: {
        'id': 1,
        'name': ''
    },
    2: {

    }
}


# Run this to load the services from the apps directory
def load_services():
    # Decide where to put the apps directory
    # Load the dictionary file with all the services.
    print("Services being Loaded")


# Route for the home page
@app.route('/', methods=['GET'])
def home():
    return "<h1>CS TV Controller</h1><p>This is the site for the CS TV API</p>"


# Route for loading services
@app.route('/reload', methods=['GET'])
def api_reload():
    load_services()


# Route for returning all available services
@app.route('/services/all', methods=['GET'])
def api_all():
    return jsonify(services)


@app.route('/services', methods=['GET'])
def api_id():
    # Check for an id in the URL.
    # If ID was provided assign it to a variable.
    # If no ID was provided display error message.
    if 'id' in request.args:
        id = int(request.args['id'])
    else:
        return 'Error: No id field provided. Please specify an id.'

    results = []

    for service in services:
        if service['id'] == id:
            results.append(service)

    return jsonify(results)

load_services()
app.run()
