"""
Main application that serves the api and contains the trained model
"""
import bottle
import pickle
import redis
import json
from sklearn import svm
from sklearn import datasets
from bottle import route, run, request, abort, static_file, get
from pymongo import MongoClient
from bson.json_util import dumps


red = redis.StrictRedis(host='localhost', port=6379, db=0)
connection = MongoClient(host='localhost', port=27017)
db = connection.stops
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
print(objects)


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


# Gets to the version 1 api for stops
@route('/apiv1/stops/', method='GET')
def get_document():
    entity = db.docs.find()
    if not entity:
        abort(404, 'No stops')
    return dumps(entity)

# Gets to the version 1 api for stop id
@route('/apiv1/stops/:stop_id', method='GET')
def get_document(stop_id):
    entity = db.docs.find_one({"id": str(stop_id)})
    if not entity:
        abort(404, 'No stop with id {}'.format(stop_id))
    return dumps(entity)

run(host='localhost', reloader=True, port=8080)
