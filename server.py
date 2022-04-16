from flask import Flask
from main import ClickHouseOperations
from flask_expects_json import expects_json

app = Flask(__name__)

@app.route("/")
def home():
    return 'Insert the event in the /api/event/ url'
    
    
@app.route("/api/event/<event>")
def event(event):
    return ClickHouseOperations(event).insert()

@app.route("/report")
@app.route('/report/<filter>')
def hello(filter=False):
    data = ClickHouseOperations(filter).read()
    return data

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)