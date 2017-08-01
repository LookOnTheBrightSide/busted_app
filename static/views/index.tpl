<!DOCTYPE html>
<html lang="en">

<head>
    <meta charset="UTF-8">
    <title>Document</title>
    <link rel="stylesheet" href="/static/css/reset.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/messenger/1.5.0/css/messenger.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/messenger/1.5.0/css/messenger-theme-flat.min.css">
    <link rel="stylesheet" type="text/css" href="/static/css/custom.css">
</head>

<%
import ast

if 'user_info' in session:
	user_info = ast.literal_eval(session['user_info'])
	user_name = user_info['name']
	user_id = user_info['id']
end
%>

<body>
	<header>
		<div id="menu">
			<a href="/" id="logo"></a>
			

			% if defined('user_name'):
			  <div id='logged_in'>{{user_name}}<div id='name'></div>
			  <div id='pic'><img src='http://graph.facebook.com/{{user_id}}/picture?type=square'></div>
			  <a href="/emissions">Emissions Tracker</a>
			  <a href="/logout">Logout</a>
			%else:
				<a href="/oauth">Login</a>

			% end

		</div>
	</header>
	<main>


		<aside>
			<div class="start_stop input_inline">
				<label for="start">From <small><span><a id="suggest_nearby_stops" href="#">find stops near me</a></span></small></label>
				<input class="search" id="start_position" name="start" type="text" placeholder="start">
				<div id="start_results" class="results_list"></div>
			</div>
			<div class="end_stop input_inline">
				<label for="end">Destination</label>
				<input class="search" id="end_position" name="end" type="text" placeholder="end">
				<div id="end_results" class="results_list"></div>
			</div>
			<div id="advanced">
				<div class="date input_inline">
					<label for="date">Date of Travel</label>
					<input class="search" id="travel_date" name="date_of_travel" type="date">
				</div>
				<div class="time input_inline">
					<label for="time">Departure Time</label>
					<input class="search" id="travel_time" name="time_of_travel" type="time" required>
				</div>
			</div>

            <div class="submission">
                <button class="button button-default" id="send_results">GO</button> <small><a id='show_advanced_options' href="#">advanced</a></small>
            </div>
            <div id="distance"></div>
            <div id="available_buses"></div>
            <div id="bus_to_destination"></div>
            <div id="bus_possibility"></div>
        </aside>
        <div id="map"></div>
    </main>
    <script src="https://code.jquery.com/jquery-3.2.1.min.js" integrity="sha256-hwg4gsxgFZhOsEEamdOYGBf13FyQuiTwlAQgxVSNgt4=" crossorigin="anonymous"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/messenger/1.5.0/js/messenger.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/messenger/1.5.0/js/messenger-theme-flat.min.js"></script>
    <script src="/static/js/app.js"></script>
    <script async defer src="https://maps.googleapis.com/maps/api/js?key=AIzaSyDZi0ETnSuaHfKU_yZX5CG2OPk55Uc7kSc&libraries=geometry,places&callback=initMap"></script>
</body>

</html>