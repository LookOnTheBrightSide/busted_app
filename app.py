"""
Main application that serves the api and contains the trained model
"""
# =============================================================
# ==================== Dependencies ===========================
# =============================================================

import bottle
from bottle import Bottle, request, run, route, redirect, response, post
import pickle
import redis
import json
import requests
from sklearn import svm
from sklearn import datasets
from bottle import route, run, request, abort, static_file, get
from pymongo import MongoClient
from bson.json_util import dumps
from bson import SON
from sklearn.externals import joblib
from requests_oauthlib import OAuth2Session
from requests_oauthlib.compliance_fixes import facebook_compliance_fix
import bottle_session
import os
from functools import wraps
import urllib.request
import datetime

# =============================================================
# ================== Install Sessions Plugin ==================
# =============================================================

app = bottle.app()
# this starts the plugin 
plugin = bottle_session.SessionPlugin(cookie_lifetime=1200)
app.install(plugin)

# =============================================================
# ================== OAUTH Global Variables LOCALHOST =========
# =============================================================

# this knocks off oauthlibs demand for https
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Credentials you get from registering a new application
client_id = '1790686954280536'
client_secret = 'f5ef9a0fd9a308c1005346770fac579c'

# OAuth endpoints given in the Facebook API documentation
authorization_base_url = 'https://www.facebook.com/dialog/oauth'
token_url = 'https://graph.facebook.com/oauth/access_token'
redirect_uri = 'http://localhost:8080/login/'     # Should match Site URL
facebook_user_profile = 'https://graph.facebook.com/me?'

# =============================================================
# ================== OAUTH Global Variables ACCUBUS.INFO=======
# =============================================================

# # Credentials you get from registering a new application
# client_id = '155589258333788'
# client_secret = 'efe7a589209ed1903bdbf65c9713ac2b'

# # OAuth endpoints given in the Facebook API documentation
# authorization_base_url = 'https://www.facebook.com/dialog/oauth'
# token_url = 'https://graph.facebook.com/oauth/access_token'
# redirect_uri = 'https://accubus.info/login/'     # Should match Site URL
# facebook_user_profile = 'https://graph.facebook.com/me?'

# =============================================================
# ================== Database Connections =====================
# =============================================================

# red = redis.StrictRedis(host='localhost', port=6379, db=0)
connection = MongoClient(host='localhost', port=27017)
db = connection.accubusDB

# ============================================================
# =================== Static Routes ==========================
# ============================================================

@bottle.get(r"/static/css/<filepath:re:.*\.css>")
def css(filepath):
    return static_file(filepath, root="static/css")

@bottle.get(r"/static/font/<filepath:re:.*\.(eot|otf|svg|ttf|woff|woff2?)>")
def font(filepath):
    return static_file(filepath, root="static/font")

@bottle.get(r"/static/img/<filepath:re:.*\.(jpg|png|gif|ico|svg)>")
def img(filepath):
    return static_file(filepath, root="static/img")

@bottle.get(r"/static/js/<filepath:re:.*\.js>")
def js(filepath):
    return static_file(filepath, root="static/js")

@bottle.get(r"/static/views/<filepath:re:.*\.html>")
def views(filepath):
    return static_file(filepath, root="static/views")

# ===================================================================
# ======================== Server End Points ========================
# ===================================================================


# ================== Home page ==============================
@bottle.route('/')
def server_static():
    return static_file('index.html', root="static/views")

# ================== All stops json ===============================

@bottle.route('/apiv1/stops/', method='GET')
def get_document():
    entity = db.stops.find()
    if not entity:
        abort(404, 'No stops')
    return dumps(entity)

# ================== Search stops on keyup =========================

@bottle.route('/apiv1/stop/:query', method='GET')
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

@bottle.route('/apiv1/route/', method='GET')
def get_all_routes():
    entity = db.routes.find({})
    return dumps(entity)

# ================== Return posible buses that serve start stop ====

@bottle.route('/apiv1/route/start/:start_stop', method='GET')
def get_stops_from_origin(start_stop):
    entity = db.routes.find({
        "route_stops.stop_id": str(start_stop)
    })
    buses = [routes['route'] for routes in entity]
    no_repeats = set(buses)
    return dumps(no_repeats)

# ====== Return posible buses that serve end stop ===================

@bottle.route('/apiv1/route/end/:end_stop', method='GET')
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

@bottle.route('/apiv1/route/start/:start_stop/end/:end_stop', method='GET')
def get_stops_from_origin(start_stop, end_stop):
    entity = db.routes.find({"$and": [{"route_stops.stop_id": str(start_stop)},
                                      {"route_stops.stop_id": str(end_stop)}]})
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

# ============== Find the 5 nearest stops =============================

@bottle.route('/apiv1/stops/:lng/:lat')
def get_nearby_stops(lat, lng):
    stops = db.stops.find(
        {"location":
         {"$near": {"$geometry": {"type": "Point",
                                  "coordinates": [float(lng), float(lat)]}}}
        }).limit(5)
    return dumps(stops)

# ============== Use Google Api so suggest connecting buses ===========

@bottle.route('/src/:src/dst/:dst', method='GET')
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

@bottle.route('/apiv1/stops/:stop_id', method='GET')
def get_document(stop_id):
    entity = db.stops.find_one({"stop_id": str(stop_id)})
    if not entity:
        abort(404, 'No stop with id {}'.format(stop_id))
    return dumps(entity)


# =============== Facebook Oauth ================================================

def validate_user(passed_function):
    """this is a decorator used to validate any endpoints."""
    @wraps(passed_function)
    def validator(*args, **kwargs):
        user_session = kwargs['session'].get('oauth_token')
        if user_session is not None:
            temp_dict = {}
            temp_dict['access_token'] = kwargs['session']['oauth_token']
            facebook = OAuth2Session(client_id, token=temp_dict)
            user_info = facebook.get(facebook_user_profile).json()
            return passed_function(kwargs['session'], user_info)
        else:
            return redirect('/')
    return validator

@bottle.route('/oauth')
def fb_login(session):
    """ask facebook for authorization code."""
    facebook = OAuth2Session(client_id, redirect_uri=redirect_uri)
    authorization_url, state = facebook.authorization_url(authorization_base_url)
    session['oauth_state'] = state
    return redirect(authorization_url)

@bottle.route('/login/', method='get')
def callback(session):
    """respond to facebook with auth code. receive token. add token to session."""
    if request.url == "http://localhost:8080/login/":
        redirect('/')
    else:
        temp_dict = {}
        facebook = OAuth2Session(client_id, redirect_uri=redirect_uri, state=session['oauth_state'])
        token = facebook.fetch_token(token_url, client_secret=client_secret, authorization_response=request.url)
        for i in token:
            temp_dict[i] = token[i]

        """if user is a new user add database entry for them"""
        user_info = facebook.get(facebook_user_profile).json()
        temp = db.user_data.find({'id': user_info['id']})
        if temp.count() == 0:
            data = {'id': user_info['id'], 'name': user_info['name']};
            db.user_data.insert_one(data);

        # here is where we put the token in the session. the session is hashed and stored as a cookie in the users browser.
        session['oauth_token'] = temp_dict['access_token']
        return redirect('/emissions')

@bottle.route('/logout', method='get')
def logout(session):
    # endpoint for the logout. send a request to facebook to log the user out. redirects to the root.
    temp_token = session['oauth_token']
    logout_url = 'https://www.facebook.com/logout.php?next=%s&access_token=%s' % (redirect_uri, temp_token)
    session.destroy()
    return redirect(logout_url)

# =============== Emissions Page ================================================

# the validate_user decorator needs the function to have session and user_info as inputs.

@bottle.route('/emissions')
@validate_user
def emissions(session, user_info):
    """returns """
    return static_file('emissions.html', root="static/views")

@bottle.route('/user_data')
@validate_user
def content(session, user_info):
    entity = db.user_data.find({'id': user_info['id']})
    return dumps(entity[0])


# =============== Run the App ==========================================
# if __name__ == "__name__":
#     run(host='localhost', reloader=True, port=8080)
# run(host='localhost', reloader=True, port=8080)
# app = bottle.default_app()

bottle.debug(True)
bottle.run(app=app, host='localhost', port='8080')
