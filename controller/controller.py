import flask
from flask import request, jsonify

app = flask.Flask(__name__)
app.config["DEBUG"] = True

# Test data for the CS TV, a list of dictionaries
services = [
    {
        'id': 0,
        'title': 'Game of Life',
    },
    {
        'id': 1,
        'title': 'Animation Video',
    },
]


# Route for the home page
@app.route('/', methods=['GET'])
def home():
    return "<h1>CS TV Controller</h1><p>This is the site for the CS TV API</p>"


# Route for returning all available services
@app.route('/services/all', methods=['GET'])
def api_all():
    return jsonify(services)


app.run()
