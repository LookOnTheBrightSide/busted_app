"""
Main application that serves the api and contains the trained model
"""
# =============================================================
# ==================== Dependencies ===========================
# =============================================================

import bottle
from bottle import Bottle, request, run, route, redirect, response, post, template
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
from requests_oauthlib import OAuth2Session
from requests_oauthlib.compliance_fixes import facebook_compliance_fix
import bottle_session
import os
from functools import wraps
import urllib.request
import time
import ast
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

# OAuth endpoints given in the Facebook API documentation
authorization_base_url = 'https://www.facebook.com/dialog/oauth'
token_url = 'https://graph.facebook.com/oauth/access_token'
redirect_uri = 'http://localhost:8080/login/'     # Should match Site URL
facebook_user_profile = 'https://graph.facebook.com/me?'

# =============================================================
# ================== OAUTH Global Variables ACCUBUS.INFO=======
# =============================================================

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
def server_static(session):
    return template('./static/views/index', session=session)

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

def get_weather_forcast():
    today = datetime.date.today()
    forecast_time = datetime.datetime(today.year, today.month, today.day, 16, 59).timestamp()
    r = requests.get('http://api.openweathermap.org/data/2.5/forecast?q=Dublin&APPID=1160274ac21e49d1ef2e0e5407489e91')
    b_time = 1
    for dt in range (0, r.json()['cnt']):
        if r.json()['list'][dt]['dt'] <= forecast_time and r.json()['list'][dt+1]['dt'] >= forecast_time:
            b_time = r.json()['list'][dt+1]['dt']
            a_time = r.json()['list'][dt]['dt']
            a = dt
            b = dt+1
    if (forecast_time - a_time) < (forecast_time - b_time):
        final_dt = a
    else:
        final_dt = b
    future_temp = r.json()['list'][final_dt]['main']['temp']-273.15
    future_wind = r.json()['list'][final_dt]['wind']['speed']
    return(future_temp,future_wind)


def predictor(start_stop_index, end_stop_index, day_of_week, hour_of_day, prediction_model,temperature,wind):
    val_start = prediction_model.predict(
        [[int(start_stop_index), day_of_week, int(hour_of_day), temperature,wind]])
    val_end = prediction_model.predict(
        [[int(end_stop_index), day_of_week, int(hour_of_day), temperature, wind]])
    return (val_end - val_start) / 60

# ====================================================================




# =============== Helper function for buses ==========================

def direct_buses(entity, start_stop, end_stop):
    buses_that_can_be_taken = []
    route_patterns = []
    buses_with_times = {}
    temperature, wind = get_weather_forcast()
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
                                                         prediction_model,temperature,wind)
    return dumps(buses_with_times)

# ====================================================================
# ======== Helper funtion to search for stop id using lat lng ========
# ====================================================================

def find_stop_id(gps_coordinates):
    # print(gps_coordinates[0], gps_coordinates[1])
    stop = db.stops.find_one({'location': {'$near': {'$geometry': {'type': 'Point', 'coordinates': [gps_coordinates[1], gps_coordinates[0]]}}}})
    # stop = db.stops.find({'location' : {'$near':}})
    # print(stop['stop_id'])
    return stop['stop_id']


@route('/apiv1/route/start/:start_stop/end/:end_stop', method='GET')
def get_stops_from_origin(start_stop, end_stop):
    entity = db.routes.find({"$and": [{"route_stops.stop_id": str(start_stop)},
                                      {"route_stops.stop_id": str(end_stop)}]})
    start_stop_gps = db.stops.find_one({"stop_id": str(start_stop)})
    end_stop_gps = db.stops.find_one({"stop_id": str(end_stop)})
    if entity.count():
        travel_details = json.loads((direct_buses(entity, start_stop, end_stop)))
        travel_details.update({"start_stop_coords": start_stop_gps['location']['coordinates'], "end_stop_coords": end_stop_gps['location']['coordinates']})
        return dumps(travel_details)
    else:
        
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
  
        # return dumps(bus_routes)
# ====================================================================
        final_directions = []
        for i in range(len(res['routes'])):
            option = {}
            # print(len(res['routes']), "...........................................")
            option['fullPolyline'] = res['routes'][i]['overview_polyline']
            for j in range(len(res['routes'][i]['legs'])):
                option['arrivalTime'] = res['routes'][i]['legs'][j]['arrival_time']['text']
                option['legDistance'] = res['routes'][i]['legs'][j]['distance']['text']
                option['legDuration'] = res['routes'][i]['legs'][j]['duration']['text']
                option['legStartAddress'] = res['routes'][i]['legs'][j]['start_address']
                option['legStartLatLng'] = [res['routes'][i]['legs'][j]['start_location']['lat'], res['routes'][i]['legs'][j]['start_location']['lng']] 
                # option['legStartStopId'] = find_stop_id(option['legStartLatLng'])
                option['legEndAddress'] = res['routes'][i]['legs'][j]['end_address']
                option['legEndLatLng'] = [res['routes'][i]['legs'][j]['start_location']['lat'], res['routes'][i]['legs'][j]['end_location']['lng']]
                # option['legEndStopId'] = find_stop_id(option['legEndLatLng'])
                for k in range(len(res['routes'][i]['legs'][j]['steps'])):
                    option['stepInstructions'] = res['routes'][i]['legs'][j]['steps'][k]['html_instructions']
                    option['stepPolyline'] = res['routes'][i]['legs'][j]['steps'][k]['polyline']['points']
                    option['stepDistance'] = res['routes'][i]['legs'][j]['steps'][k]['distance']['text']
                    option['stepDuration'] = res['routes'][i]['legs'][j]['steps'][k]['duration']['text']
                    try:
                        option['transitArrivalStopLatLng'] = [res['routes'][i]['legs'][j]['steps'][k]['transit_details']['arrival_stop']['location']['lat'],
                        res['routes'][i]['legs'][j]['steps'][k]['transit_details']['arrival_stop']['location']['lng']]
                        # option['transitArrivalStopId'] = find_stop_id(option['transitArrivalStopLatLng'])
                        option['transitArrivalStopName'] = res['routes'][i]['legs'][j]['steps'][k]['transit_details']['arrival_stop']['name']

                        option['transitDepartureStopLatLng'] = [res['routes'][i]['legs'][j]['steps'][k]['transit_details']['departure_stop']['location']['lat'],
                        res['routes'][i]['legs'][j]['steps'][k]['transit_details']['departure_stop']['location']['lng']]
                        # option['transitDepartureStopId'] = find_stop_id(option['transitDepartureStopLatLng'])
                        option['transitDepartureStopName'] = res['routes'][i]['legs'][j]['steps'][k]['transit_details']['departure_stop']['name']

                        option['transitNumberOfStops'] = res['routes'][i]['legs'][j]['steps'][k]['transit_details']['num_stops']
                        option['transitHeadSign'] = res['routes'][i]['legs'][j]['steps'][k]['transit_details']['headsign']
                        option['transitBusName'] = res['routes'][i]['legs'][j]['steps'][k]['transit_details']['line']['short_name']
                    except Exception as ex:
                        # print(ex)
                        pass    
                        
            option['legStartStopId'] = find_stop_id(option['legStartLatLng'])
            option['legEndStopId'] = find_stop_id(option['legEndLatLng'])
            option['transitArrivalStopId'] = find_stop_id(option['transitArrivalStopLatLng'])
            option['transitDepartureStopId'] = find_stop_id(option['transitDepartureStopLatLng'])
            option['accubusPrediction'] = ()
            final_directions.append(option)

                    

        # return dumps(final_directions)
        # return response.json()
        # print(res['routes'][0]['legs'][0]['end_location'])
        # vals = 
        return dumps({'start_stop_coords':[res['routes'][0]['legs'][0]['start_location']['lng'], \
            res['routes'][0]['legs'][0]['start_location']['lat']],
         'end_stop_coords':[res['routes'][0]['legs'][0]['end_location']['lng'],\
         res['routes'][0]['legs'][0]['end_location']['lat']]})

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

# @bottle.route('/src/:src/dst/:dst', method='GET')
# def get_document(src, dst):
#     src = src.replace('_', '+')
#     dst = dst.replace('_', '+')
#     google_api_url = ("""https://maps.googleapis.com/maps/api/directions/json?
#         origin={}&destination={}&mode=transit&sensor=false&transit_mode=bus&
#         key=AIzaSyCVxRxsS43t9mXRFz80L3uSCo2ZfrsA_40""").format(src, dst)
#     directions = requests.get(google_api_url)
#     result = directions.json()
#     # temp = []
#     # for i in range(0, len(result["routes"][0]["legs"][0]["steps"])):
#     #     temp.append(result["routes"][0]["legs"][0]["steps"][i]["html_instructions"])
#     return dumps(result)

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
            
            templist = []
            templist.append(kwargs['session'])
            del kwargs['session']

            for i in kwargs:
                templist.append(kwargs[i])
            return passed_function(*templist)
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
    if request.url == redirect_uri:
        redirect('/')
    else:
        temp_dict = {}
        facebook = OAuth2Session(client_id, redirect_uri=redirect_uri, state=session['oauth_state'])
        token = facebook.fetch_token(token_url, client_secret=client_secret, authorization_response=request.url)
        for i in token:
            temp_dict[i] = token[i]

        """if user is a new user add database entry for them"""
        user_info = facebook.get(facebook_user_profile).json()
        # temp = db.user_data.find({'id': user_info['id']})

        db.user_data.find_one_and_update({'_id': user_info['id']},
         {'$set': {'name': user_info['name']}}, upsert=True)
        db.user_data.find_one_and_update({'_id': user_info['id']},
         {'$set': {'car_tax': 'c'}}, upsert=True)
        db.user_data.find_one_and_update({'_id': user_info['id']},
         {'$push': {'last_login': time.time()}}, upsert=True)

        # here is where we put the token in the session. the session is hashed and stored as a cookie in the users browser.
        session['oauth_token'] = temp_dict['access_token']
        session['user_info'] = user_info
        return redirect('/')

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
def emissions(session):
    """returns"""
    return static_file('emissions.html', root="static/views")

@bottle.route('/user_data')
@validate_user
def content(session):
    # entity = db.user_data.find({'_id': user_info['id']})
    user_info = ast.literal_eval(session['user_info'])
    return dumps(db.user_data.find({'_id': user_info['id']})[0])

@bottle.route('/add_car_tax/:car_tax', method='GET')
@validate_user
def set_car_tax(session, car_tax):

    user_info = ast.literal_eval(session['user_info'])
    db.user_data.find_one_and_update({'_id': user_info['id']},
        {'$set': {'car_tax': car_tax}}, upsert=True)
    return car_tax

@bottle.route('/add_route_data/:route/:distance', method='GET')
@validate_user
def add_route_data(session, route, distance):
    # sample_journey = {"start_point": [-6.264897288,53.31704597], "end_point": [-6.256110584,53.29510352], "legs": [{"mode": "walk", "distance": .5}, {"mode": "bus", "jpid": "00161001", "distance": .5}]}
    user_info = ast.literal_eval(session['user_info'])
    find_user = db.user_data.find({'_id': user_info['id']})
    sample_journey = [find_user[0]['car_tax'], route, distance]
    db.user_data.find_one_and_update({'_id': user_info['id']},
         {'$push': {'journey': sample_journey}}, upsert=True)
    temp = [["added"]]
    return dumps(temp)

@bottle.route('/get_journey/', method='GET')
@validate_user
def add_journey(session):

    user_info = ast.literal_eval(session['user_info'])
    result = {}
    band = db.user_data.find_one({'_id': user_info['id']})['car_tax']
    result['journey'] = db.user_data.find_one({'_id': user_info['id']})
    return dumps(result)

def band_to_c02(band):
    if band == 'a0':
        c02 = 0
    elif band == 'a1':
        c02 = 80
    elif band == 'a2':
        c02 = 100
    elif band == 'a3':
        c02 = 110
    elif band == 'a4':
        c02 = 120
    elif band == 'b1':
        c02 = 130
    elif band == 'b2':
        c02 = 140
    elif band == 'c':
        c02 = 155
    elif band == 'd':
        c02 = 170
    elif band == 'e':
        c02 = 190
    elif band == 'f':
        c02 = 225
    else:
        c02 = 250
    return c02

# =============== Run the App ================================================

# # run on server
# app = bottle.default_app()

# run locally for dev
bottle.debug(True)
bottle.run(app=app, host='localhost', port='8080')



