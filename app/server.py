from flask import Flask
from main import ClickHouseOperations

app = Flask(__name__)

@app.route("/")
def home():
    return 'Insert the event in the /api/event/ url'
    
    
@app.route("/api/event/<event>")
def insert(event):
    return ClickHouseOperations(event).insert()

@app.route("/api/report")
@app.route('/api/report/<filter>')
def read(filter=False):
    data = ClickHouseOperations(filter).read()
    return data

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)