from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
@app.route("/health", methods=["GET"])
def health_check():
    return {"status": "OK"}

@app.route("/count", methods=["GET"])
def count_documents():
    count = db.songs.count_documents({})
    return {"count": count}, 200

@app.route("/song", methods=["GET"])
def get_songs():
    # Vyhledání všech písní v kolekci 'songs'
    all_songs = db.songs.find({})
    # Převod na seznam
    songs_list = [parse_json(song) for song in all_songs]
    # Vrácení seznamu písní s kódem 200
    return {"songs": songs_list}, 200

@app.route("/song/<int:id>", methods=["GET"])
def get_song_by_id(id):
    # Vyhledání písně podle ID
    song = db.songs.find_one({"id": id})
    if song:
        # Pokud je píseň nalezena, vrátí ji jako JSON s kódem 200
        return parse_json(song), 200
    else:
        # Pokud není nalezena, vrátí zprávu s kódem 404
        return {"message": "song with id not found"}, 404

@app.route("/song", methods=["POST"])
def create_song():
    # Extrahování dat z těla požadavku
    song_data = request.get_json()

    # Zjištění, zda již existuje píseň s tímto ID
    existing_song = db.songs.find_one({"id": song_data["id"]})

    if existing_song:
        # Pokud píseň již existuje, vrátí chybovou zprávu s kódem 302
        return {"Message": f"song with id {song_data['id']} already present"}, 302

    # Pokud ne, vloží novou píseň do databáze
    result = db.songs.insert_one(song_data)

    # Vrátí ID nově vložené písně s kódem 201
    return {"inserted id": str(result.inserted_id)}, 201

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    # Extrahování dat písně z těla požadavku
    new_data = request.json
    
    # Vyhledání písně podle ID
    song = db.songs.find_one({"id": id})
    
    if song:
        # Pokud je píseň nalezena, aktualizujte ji
        db.songs.update_one({"id": id}, {"$set": new_data})
        updated_song = db.songs.find_one({"id": id})
        return parse_json(updated_song), 200
    else:
        # Pokud není píseň nalezena, vrátí zprávu s kódem 404
        return {"message": "song not found"}, 404

@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    # Odstranění písně podle ID
    result = db.songs.delete_one({"id": id})

    if result.deleted_count == 0:
        # Pokud není nalezena píseň, vrátí 404
        return {"message": "song not found"}, 404
    else:
        # Pokud je píseň smazána, vrátí 204 bez obsahu
        return '', 204