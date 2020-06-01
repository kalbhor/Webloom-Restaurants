from flask import Flask, jsonify, url_for, redirect, request
from flask_restful import Api, Resource
import bson.json_util as json_util
from dateutil import parser
import pymongo
import json
from bson.objectid import ObjectId

app = Flask(__name__)
client = pymongo.MongoClient()
db = client['main']
APP_URL = "http://127.0.0.1:5000"


class Booking(Resource):
    def get(self,_id=None,restaurant_id=None,date=None, time=None):
        search = {"_id" : _id, "restaurant_id" : restaurant_id, "date" : date, "time" : time}
        search = {k: v for k, v in search.items() if v is not None} # Remove keys where val is nonetype

        bookings = db['bookings'].find(search, {"_id": 0})
        bookings = json.loads(json_util.dumps(bookings))

        if bookings:
            return jsonify({"status": "ok", "data": bookings})
        else:
            return {"response": "no bookings found for {}".format(date)}


    def post(self):
        data = request.get_json()
        if not data:
            data = {"response": "ERROR"}
            return jsonify(data)
        else:
            return "ok"



class Table(Resource):
    def get(self):
        search_params = self.marshall(request.get_json(), request_method="GET")

        tables = db['tables'].find(search_params, {"_id": 0})
        tables = json.loads(json_util.dumps(tables))

        if tables:
            return jsonify({"status": "ok", "data": tables})
        else:
            return {"response": "no tables found for {}".format(search)}


    def post(self):
        insertion = self.marshall(request.get_json(), request_method="POST")
        if not insertion:
            return jsonify({"response": "ERROR"})
        else:
            restaurant_id = insertion['restaurant_id']
            table_size = insertion['size']
            if restaurant_id and table_size:
                result = db['tables'].insert_one(data)
                _id = result.inserted_id
                return {"response" : "Table added with id {}".format(str(_id))}
            else:
                return {"response": "Restaurant id or table size missing"}

    def marshall(self, data, request_method):
        if request_method == "GET":
            print('ok1')
            search = {"_id" : data.get("id"), "restaurant_id" : data.get("restaurant_id"), "size" : data.get("size")}
            search = {k: v for k, v in search.items() if v is not None} # Remove keys where val is nonetype
            if data.get("booking_id"):
                search["booking_ids"] = {"$elemMatch" : data.get("booking_id")}
            return search

        elif request_method == "POST":
            #Do marshalling here
            print('ok2')
            return data

class Restaurant(Resource):
    def get(self):
        admin = (request.get_json()).get("admin")
        print(request.get_json())
        search_params = self.marshall(request.get_json(), request_method="GET")

        if admin:
            print(admin)
            restaurants = db['restaurant'].find(search_params)
        else:
            print('ok')
            restaurants = db['restaurant'].find(search_params, {"_id": 0})

        restaurants = json.loads(json_util.dumps(restaurants))

        if restaurants:
            return jsonify({"status": "ok", "data": restaurants})
        else:
            return {"response": "No bookings found for {}".format(search)}


    def post(self):
        insertion = self.marshall(request.get_json(), request_method="POST")
        if not insertion:
            return jsonify({"response": "ERROR"})
        else:
            restaurant_name = insertion.get('name')
            if restaurant_name:
                if db['restaurant'].find_one({"name": restaurant_name}):
                    return {"response": "Restaurant already exists."}
                else:
                    result = db['restaurant'].insert_one(insertion)
                    _id = result.inserted_id
                    return {"response" : "Restaurant added with id {}".format(str(_id))}
            else:
                return {"response": "Restaurant name missing"}

    def marshall(self, data, request_method):
        if request_method == "GET":
            print('ok1')
            search = {"_id" : data.get("id"), "name" : data.get("name")}
            search = {k: v for k, v in search.items() if v is not None} # Remove keys where val is nonetype
            return search

        elif request_method == "POST":
            #Do marshalling here
            print('ok2')
            return data

api = Api(app)
api.add_resource(Booking, "/api/bookings")
api.add_resource(Restaurant, "/api/restaurants")
api.add_resource(Table, "/api/tables")

if __name__ == "__main__":
    app.run(debug=True)
