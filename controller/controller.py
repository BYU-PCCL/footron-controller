import flask

app = flask.Flask(__name__)
app.config["DEBUG"] = True

@app.route('/', methods=['GET'])
def home():
    return "<h1>CS TV Controller</h1><p>This is the site for the CS TV API</p>"

app.run()
