"""
Main application that serves the api and contains the trained model
"""
# =============================================================
# ==================== Dependencies ===========================
# =============================================================

import bottle
import pickle
import redis
import json
import re
import requests
from keys import *
from sklearn import svm
from sklearn import datasets
from bottle import route, run, request, abort, static_file, get
from pymongo import MongoClient
from bson.json_util import dumps
from bson import SON
from sklearn.externals import joblib

# =============================================================
# ================== Database Connections =====================
# =============================================================

# red = redis.StrictRedis(host='localhost', port=6379, db=0)
connection = MongoClient(host='localhost', port=27017)
db = connection.accubusDB

# ============================================================
# =================== Static Routes ==========================
# ============================================================

@get(r"/static/css/<filepath:re:.*\.css>")
def css(filepath):
    return static_file(filepath, root="static/css")


@get(r"/static/font/<filepath:re:.*\.(eot|otf|svg|ttf|woff|woff2?)>")
def font(filepath):
    return static_file(filepath, root="static/font")


@get(r"/static/img/<filepath:re:.*\.(jpg|png|gif|ico|svg)>")
def img(filepath):
    return static_file(filepath, root="static/img")


@get(r"/static/js/<filepath:re:.*\.js>")
def js(filepath):
    return static_file(filepath, root="static/js")


@get(r"/static/views/<filepath:re:.*\.html>")
def views(filepath):
    return static_file(filepath, root="static/views")

# ===================================================================
# ======================== Server End Points ========================
# ===================================================================


# ================== Home page ==============================
@route('/')
def server_static():
    return static_file('index.html', root="static/views")

# ================== All stops json ===============================


@route('/apiv1/stops/', method='GET')
def get_document():
    entity = db.stops.find()
    if not entity:
        abort(404, 'No stops')
    return dumps(entity)

# ================== Search stops on keyup =========================


@route('/apiv1/stop/:query', method='GET')
def get_stop(query):
    """"search by stop_id, address, stop_name - case insensitive"""
    if query != "":
        entity = db.stops.find({'$or': [
            {'stop_id': {'$regex': '^{}'.format(query), '$options': 'i'}},
            {'address': {'$regex': '^{}'.format(query), '$options': 'i'}},
            {'stop_name': {'$regex': '^{}'.format(query), '$options': 'i'}}
        ]})
    return dumps(entity)

# ================== All routes json ===============================


@route('/apiv1/route/', method='GET')
def get_all_routes():
    entity = db.routes.find({})
    return dumps(entity)

# ================== Return posible buses that serve start stop ====


@route('/apiv1/route/start/:start_stop', method='GET')
def get_stops_from_origin(start_stop):
    entity = db.routes.find({
        "route_stops.stop_id": str(start_stop)
    })
    buses = [routes['route'] for routes in entity]
    no_repeats = set(buses)
    return dumps(no_repeats)

# ====== Return posible buses that serve end stop ===================


@route('/apiv1/route/end/:end_stop', method='GET')
def get_stops_from_destination(end_stop):
    entity = db.routes.find({
        "route_stops.stop_id": str(end_stop)
    })
    buses = [routes['route'] for routes in entity]
    no_repeats = set(buses)
    return dumps(no_repeats)

# ====================================================================
# checks which buses can be taken
# checks if both buses are on the same route and
# that end stop comes after start stop
# ***************** Fututre ******************************************
# * check if the time entered is served by bus*
# ====================================================================
# ==================== Helper Method =================================


def predictor(start_stop_index, end_stop_index, day_of_week, hour_of_day, prediction_model):
    val_start = prediction_model.predict(
        [int(start_stop_index), day_of_week, int(hour_of_day)])
    val_end = prediction_model.predict(
        [int(end_stop_index), day_of_week, int(hour_of_day)])
    return (val_end - val_start) / 60

# ====================================================================



# =============== Helper function for buses ==========================
def direct_buses(entity, start_stop, end_stop):
    buses_that_can_be_taken = []
    route_patterns = []
    buses_with_times = {}
    for i in entity:
        for j in i['route_stops']:
            if j['stop_id'] == str(start_stop):
                start_index = j['stop_index']
            if j['stop_id'] == str(end_stop):
                end_index = j['stop_index']
        if start_index < end_index:
            buses_that_can_be_taken.append(i["route"])
            route_patterns.append(i["route_pattern_id"])
            if "models/{}.pk1".format(i["route_pattern_id"]):
                prediction_model = joblib.load(
                    "models/{}.pk1".format(i["route_pattern_id"]))
                buses_with_times[i["route"]] = predictor(start_index, end_index, 3, 5,
                                                         prediction_model)
    return dumps(buses_with_times)

# ====================================================================


@route('/apiv1/route/start/:start_stop/end/:end_stop', method='GET')
def get_stops_from_origin(start_stop, end_stop):
    entity = db.routes.find({"$and": [{"route_stops.stop_id": str(start_stop)},
                                      {"route_stops.stop_id": str(end_stop)}]})
    if entity.count():
        return direct_buses(entity, start_stop, end_stop)
    else:
        start_stop_gps = db.stops.find_one({"stop_id": str(start_stop)})
        end_stop_gps = db.stops.find_one({"stop_id": str(end_stop)})
        query_path = """https://maps.googleapis.com/maps/api/directions/json?origin=
                        {},{}&destination={},{}&alternatives=true&
                        mode=transit&key={}
                        """.format(
                            float(start_stop_gps['location']['coordinates'][1]),
                            float(start_stop_gps['location']['coordinates'][0]),
                            float(end_stop_gps['location']['coordinates'][1]),
                            float(end_stop_gps['location']['coordinates'][0]), MAP_KEY)

        trimmer = re.compile(r'\s+')
        path = trimmer.sub('', query_path)
        response = requests.get(path)

        # print(type(response))

        # result = json.loads(response)
        # print(type(result))
        bus_routes = {}
        res = response.json()
        print(res['routes'])
        for i in res:
            for j in res['routes']:
                for k in j['legs']:
                    bus_routes['Final Destination'] = k['end_address']
                    bus_routes['Start Address'] = k['start_address']
                    for l in k['steps']:
                        bus_routes['For Distance Of'] = k['distance']['text']
                        bus_routes['Instructions'] = l['html_instructions']
                        bus_routes['Polyline'] = l['polyline']['points']
                        # bus_routes['Transit Details'] = l['transit_details']['name']
                        # bus_routes['Take Bus'] = l['line']['short_name']
        return dumps(bus_routes)
        # return response.json()

# ============== Find the 5 nearest stops =============================


@route('/apiv1/stops/:lng/:lat')
def get_nearby_stops(lat, lng):
    stops = db.stops.find(
        {"location":
         {"$near": {"$geometry": {"type": "Point",
                                  "coordinates": [float(lng), float(lat)]}}}
        }).limit(5)
    return dumps(stops)

# ============== Use Google Api so suggest connecting buses ===========


@route('/src/:src/dst/:dst', method='GET')
def get_document(src, dst):
    src = src.replace('_', '+')
    dst = dst.replace('_', '+')
    google_api_url = ("""https://maps.googleapis.com/maps/api/directions/json?
        origin={}&destination={}&mode=transit&sensor=false&transit_mode=bus&
        key=AIzaSyCVxRxsS43t9mXRFz80L3uSCo2ZfrsA_40""").format(src, dst)
    directions = requests.get(google_api_url)
    result = directions.json()
    # temp = []
    # for i in range(0, len(result["routes"][0]["legs"][0]["steps"])):
    #     temp.append(result["routes"][0]["legs"][0]["steps"][i]["html_instructions"])
    return dumps(result)

# =============== Get stop id ==========================================


@route('/apiv1/stops/:stop_id', method='GET')
def get_document(stop_id):
    entity = db.stops.find_one({"stop_id": str(stop_id)})
    if not entity:
        abort(404, 'No stop with id {}'.format(stop_id))
    return dumps(entity)


# =============== Run the App ==========================================
# if __name__ == "__name__":
#     run(host='localhost', reloader=True, port=8080)
run(host='localhost', reloader=True, port=8088)
# app = bottle.default_app()
# app = bottle.default_app()
