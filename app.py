"""
Main application that serves the api and contains the trained model
"""
import bottle
import pickle
import redis
import json
from xgboost import XGBClassifier
from sklearn import svm
from sklearn import datasets
from bottle import route, run, request, abort, static_file, get
from pymongo import MongoClient
from bson.json_util import dumps


red = redis.StrictRedis(host='localhost', port=6379, db=0)
connection = MongoClient('mongodb://127.0.0.1:27017/', connect=False)
db = connection.stops
db_routes = connection.routes
# =========================

# clf = svm.SVC()
# iris = datasets.load_iris()
# X, y = iris.data, iris.target
# clf.fit(X, y)
# s = pickle.dumps(clf)
# pickle_in = open('random_forest_test_pickle.obj','rb')
# clf2 = pickle.loads(pickle_in)
objects = []
with (open("random_forest_test_pickle.obj", "rb")) as openfile:
    while True:
        try:
            objects.append(pickle.load(openfile))
        except EOFError:
            break
# print(objects)
#pickle_in = open('random_forest.sav', 'rb')
#prediction_model = pickle.load(pickle_in)

# station_one = y[0]
# =========================

# Static Routes ===========
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
# end of static routes

# Home page
@route('/')
def server_static():
    return static_file('index.html', root="static/views")

# Test end point - must be deleted
@route('/one')
def server_one():
    res = objects[0].predict([1, 0.105961, 0.000000, 0.285714])
    return "{} prediction".format(res)

# Get all routes 
@route('/apiv1/route/', method='GET')
def get_all_routes():
    entity = db_routes.docs.find()
    return dumps(entity)

# Get one route
@route('/apiv1/route/:route_num', method='GET')
def get_single_route(route_num):
    entity = db_routes.docs.find({"route":str(route_num)})
    if not entity:
        abort(404, "No route {} found".format(route_num))
    return dumps(entity)

@route('/apiv1/route/:route_num/:start_stop/:end_stop/:departure_time', method='GET')
def get_travel_time(route_num, start_stop, end_stop, departure_time):
    entity = db_routes.docs.find({"route":str(route_num)})
    pickle_in = open('LR_model.sav', 'rb')
    prediction_model = pickle.load(pickle_in)
    val_start = prediction_model.predict([int(start_stop), -54, int(departure_time)])
    val_end = prediction_model.predict([int(end_stop), -183, int(departure_time)])
    return "Accubus says it will take {} mins".format((val_end - val_start)/60)
        

# Gets to the version 1 api for stops
@route('/apiv1/stops', method='GET')
def get_document():
    entity = db.docs.find()
    if not entity:
        abort(404, 'No stops')
    return dumps(entity)

# Gets to the version 1 api for stop id
@route('/apiv1/stops/:stop_id', method='GET')
def get_document(stop_id):
    entity = db.docs.find_one({"stop_id": str(stop_id)})
    if not entity:
        abort(404, 'No stop with id {}'.format(stop_id))
    return dumps(entity)
app = bottle.default_app()
# run(host='localhost', reloader=True, port=8080)
