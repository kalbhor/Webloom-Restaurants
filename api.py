from flask import Flask, jsonify, url_for, redirect, request
from flask_restful import Api, Resource
import bson.json_util as json_util
from dateutil import parser
import pymongo
import json
from datetime import timedelta
from bson.objectid import ObjectId

app = Flask(__name__)
client = pymongo.MongoClient()
db = client['main']
RESERVATION_HOURS = 2
APP_URL = "http://127.0.0.1:5000"


class Booking(Resource):
    def get(self):
        search_params = self.marshall(request.args, request_method="GET")
        if search_params.get('_id'):
            # Convert to Mongo readable ID object
            search_params['_id'] = ObjectId(search_params['_id'])

        bookings = db['bookings'].find(search_params)
        bookings = json.loads(json_util.dumps(bookings))

        if bookings:
            return jsonify({"status": "ok", "data": bookings})
        else:
            return {"response": "no bookings found for {}".format(search_params)}


    def post(self):
        insertion = self.marshall(request.get_json(), request_method="POST")
        if not insertion:
            return jsonify({"response": "ERROR"})
        else:
            # Check if booking is valid (tables available, no timeslot overlap, etc)
            data = self.verify(insertion)

            if data['status'] is not "ok":
                return data['status']

            insertion = data['data']
            result = db['bookings'].insert_one(insertion)
            _id = result.inserted_id
            table_ids = insertion['table_ids']

            # Add booking id to all tables booked
            for table_id in table_ids:
                write_concern = db['tables'].update_one({"_id" : ObjectId(table_id)}, {"$push" : {"bookings" : _id}})

            return {"response" : "Booking added with id {}".format(str(_id))}

    def marshall(self, data, request_method):
        if request_method == "GET":
            if not data:
                data = {}
            search = {"_id" : data.get("id"), "name" : data.get("name"),
                      "restaurant_id" : data.get("restaurant_id"),
                      "date" : data.get("date"),
                      "time" : data.get("time")
                      }
            search = {k: v for k, v in search.items() if v is not None} # Remove keys where val is nonetype
            if data.get("table_id"):
                search["table_ids"] = {"$elemMatch" : {"$eq" : data.get("table_id")}},
            return search

        elif request_method == "POST":
            data['date'] = parser.parse(data['date'])
            data['time_start'] = parser.parse(data['time'])
            data['time_end'] = data['time_start'] + timedelta(hours=RESERVATION_HOURS)
            del data['time']
            ## Manage if time exceeds into next date

            #Do marshalling here (check if all params are present)
            return data

    def potential(self, data):
        """
        This method finds all potential tables for a booking.
        Potential tables are all tables with either table size = booking size or if the tables are flexible
        """

        fixed_ids = [] # A list of all tables that match the size of booking
        flexible_ids = [] # A list of all flexible tables

        tables = db['tables'].find({"size" : data['size']})
        tables = json.loads(json_util.dumps(tables))
        for table in tables:
            table_id = table['_id']['$oid']
            fixed_ids.append(table_id)


        tables = db['tables'].find({"flexible" : True})
        tables = json.loads(json_util.dumps(tables))
        for table in tables:
            table_id = table['_id']['$oid']
            flexible_ids.append(table_id)

        return {"fixed" : fixed_ids, "flexible" : flexible_ids}

    def booked(self, data):
        """
        This method finds all the potential tables booked during the requested booking timeslot.
        """
        booked_ids = []

        ## Search for all tables booked during specified time slot
        search_params = {"restaurant_id" : data['restaurant_id'],
                        "date" : data['date'],
                        "time_start" : {'$lt' : data['time_end']},
                        "time_end" : {'$gt' : data['time_start']},
                        "$or" : [{'size' : data['size']}, {'flexible' : True}]
                        }

        bookings = db['bookings'].find(search_params)
        bookings = json.loads(json_util.dumps(bookings))
        for booking in bookings:
            for table_id in booking['table_ids']:
                booked_ids.append(table_id)

        return booked_ids


    def verify(self, data):
        """
        This method checks whether the requested booking is possible or not. 
        It find the potential tables and the booked potential tables. 
        """

        potential_tables = self.potential(data)
        fixed_ids = potential_tables['fixed']
        flexible_ids = potential_tables['flexible']

        booked_ids = self.booked(data)

        ## Gets the tables in potential tables that are not booked
        fixed_available_ids = list(set(fixed_ids) - set(booked_ids))
        flexible_available_ids = list(set(flexible_ids) - set(booked_ids))

        if len(fixed_available_ids) > 0:
            # There is a table with the exact size as requested
            data['table_ids'] = [fixed_available_ids[0]]
            return {"status" : 'ok', "data" : data}

        elif len(flexible_available_ids) > 0:
            # There are no tables with exact size, so find if possible to use combo of flexible tables
            flexible_size = 0
            flexible_ids = []

            flexible_available_ids = [ObjectId(elem) for elem in flexible_available_ids]

            tables = db['tables'].find({"_id" : {"$in" : flexible_available_ids}})
            tables = json.loads(json_util.dumps(tables))

            for table in tables:
                flexible_size = flexible_size + table['size']
                flexible_ids.append(table["_id"]["$oid"])
                if flexible_size >= data['size']:
                    # If combo of flexible tables is equal or greater than requested size
                    data['table_ids'] = flexible_ids
                    return {"status" : "ok", "data" : data}

        return {'status' : 'No tables found'}



class Table(Resource):
    def get(self):
        search_params = self.marshall(request.args, request_method="GET")
        if search_params.get('_id'):
            search_params['_id'] = ObjectId(search_params['_id'])

        tables = db['tables'].find(search_params)
        tables = json.loads(json_util.dumps(tables))

        if tables:
            return jsonify({"status": "ok", "data": tables})
        else:
            return {"response": "no tables found for {}".format(search_params)}


    def post(self):
        insertion = self.marshall(request.get_json(), request_method="POST")
        if not insertion:
            return jsonify({"response": "ERROR"})
        else:
            restaurant_id = insertion['restaurant_id']
            table_size = insertion['size']
            if restaurant_id and table_size:
                result = db['tables'].insert_one(insertion)
                _id = result.inserted_id

                # Add table id to restaurant
                write_concern = db['restaurants'].update_one({"_id" : ObjectId(restaurant_id)}, {"$push" : {"tables" : _id}})

                return {"response" : "Table added with id {}".format(str(_id))}
            else:
                return {"response": "Restaurant id or table size missing"}

    def marshall(self, data, request_method):


        data = {} if data is None else data

        if request_method == "GET":
            search = {"_id" : data.get("id"), "restaurant_id" : data.get("restaurant_id"), 
                    "size" : data.get("size"), "flexible" : data.get("flexible"), "bookings" : data.get("bookings")}

            search = {k: v for k, v in search.items() if v is not None} # Remove keys where val is nonetype
            if data.get("booking_id"):
                search["booking_ids"] = {"$elemMatch" : data.get("booking_id")}
            
            return search

        elif request_method == "POST":
            #Do marshalling here
            data = {k: v for k, v in data.items() if v is not None} # Remove keys where val is nonetype
            data['flexible'] = False if data.get('flexible') is None else data.get('flexible')
            data['bookings'] = [] if data.get('bookings') is None  else data.get('bookings')

            return data

class Restaurant(Resource):
    def get(self):


        search_params = self.marshall(request.args, request_method="GET")
        if search_params.get('_id'):
            search_params['_id'] = ObjectId(search_params['_id'])

        restaurants = db['restaurants'].find(search_params)
        restaurants = json.loads(json_util.dumps(restaurants))

        if restaurants:
            return jsonify({"status": "ok", "data": restaurants})
        else:
            return {"response": "No results found for {}".format(search_params)}


    def post(self):
        insertion = self.marshall(request.get_json(), request_method="POST")
        if not insertion:
            return jsonify({"response": "ERROR"})
        else:
            restaurant_name = insertion.get('name')
            if restaurant_name:
                if db['restaurants'].find_one({"name": restaurant_name}):
                    return {"response": "Restaurant already exists."}
                else:
                    result = db['restaurants'].insert_one(insertion)
                    _id = result.inserted_id
                    return {"response" : "Restaurant added with id {}".format(str(_id))}
            else:
                return {"response": "Restaurant name missing"}

    def marshall(self, data, request_method):
        if request_method == "GET":
            if not data:
                data = {}
            search = {"_id" : data.get("id"), "name" : data.get("name")}
            search = {k: v for k, v in search.items() if v is not None} # Remove keys where val is nonetype
            return search

        elif request_method == "POST":
            if data.get("name") is None:
                # Throw some error
                return None
            if data.get("tables") is None:
                data['tables'] = []
                
            #Do marshalling here
            return data

api = Api(app)
api.add_resource(Booking, "/api/bookings")
api.add_resource(Restaurant, "/api/restaurants")
api.add_resource(Table, "/api/tables")

if __name__ == "__main__":
    app.run(debug=True)
