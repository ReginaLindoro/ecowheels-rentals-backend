# app.py
from flask import Flask, jsonify, request
from pymongo import MongoClient
import certifi
ca = certifi.where()

app = Flask(__name__)

# MongoDB configuration
client = MongoClient("mongodb+srv://reginalindoro:JsUcVf06cZLTr37d@cluster0.oxbejdf.mongodb.net/?retryWrites=true&w=majority", tlsCAFile=ca)
db = client.test

@app.route('/insert', methods=['POST'])
def insert_data():
    data = request.get_json()
    collection = db['test_collection']  # Replace with the collection name
    inserted_data = collection.insert_one(data)
    return jsonify(str(inserted_data.inserted_id))

if __name__ == '__main__':
    app.run(debug=True)
