$(document).ready(function() {

    var total_time = 0;
    // =============== Unix Time Getter ===================
    Date.prototype.getUnixTime = function() { return this.getTime()/1000|0 };
    if(!Date.now) Date.now = function() { return new Date(); }
    Date.time = function() { return Date.now().getUnixTime(); }
    // ====================================================
    // ===========Pull live data from dublin bus api=======
    // ====================================================
    var pull_live_data = function(start_stop_id) {
        $.getJSON(`https://data.dublinked.ie/cgi-bin/rtpi/realtimebusinformation?stopid=${start_stop_id}&format=json`, function(live_data) {
            if (live_data.results.length) {
                // if($('#bus_possibility')){
                //     $('#bus_possibility').html('');
                // }
                $('#bus_possibility').append(`<h5>Next Buses</h5>`);
                for (var i = 0; i < live_data.results.length; i++) {
                    $('#bus_possibility').append(`<span id="chosen_bus" class="bus_to_take button-small">${live_data.results[i].route} bus to ${live_data.results[i].destination} in ${live_data.results[i].duetime} mins</span>`);
                }
            }
        });
    }

    // ===============================
    // Initial setup for notifications
    // ===============================
    Messenger.options = {
        extraClasses: 'messenger-fixed messenger-on-top messenger-on-right',
        theme: 'flat',
        'messageDefaults': {
            hideAfter: 3
        }
    }

    // =====================================================

    $('div.add_emissions:empty').hide();
    document.getElementById("add_emissions").addEventListener("click", function(){
        var distance = $("#emission_distance").text();
        $.getJSON(`/add_route_data/00161001/${distance}`, {}, function(data) {

            Messenger().post({
                message: 'Journey added to emissions tracker!',
                type: 'success',
                showCloseButton: true
            });

            // $('#add_emission_result').append("<div>Journey Added!</div>");
        });
    });

    $('div.add_subscribe:empty').hide();
    document.getElementById("add_subscribe").addEventListener("click", function(){
        var start_position = $("#start_position").val();
        var end_position = $("#end_position").val();

        start_stop = start_position.split(" ")[0];
        end_stop = end_position.split(" ")[0];

        if (document.getElementById('daily').checked) {
          var freq = document.getElementById('daily').value;
        }
        if (document.getElementById('weekly').checked) {
          var freq = document.getElementById('weekly').value;
        }
        if (document.getElementById('workdays').checked) {
          var freq = document.getElementById('workdays').value;
        }

        var input_selected = new Date().getUnixTime();
        if($("#arrival_time").val()){
            var user_date = $("#arrival_time").val();
            input_selected = new Date(user_date).getUnixTime();
        }


// /apiv1/create_subscribe/:number/:start_stop/:end_stop/:freq
    $.getJSON(`/apiv1/create_subscribe/${start_stop}/${end_stop}/${freq}/${input_selected}`, {}, function(data) {
        if (data.status == 'No Phone Number'){

        Messenger().post({
            message: 'You need to enter your phone number of the emissions page!!',
            type: 'failure',
            showCloseButton: true
        });

        } else {

        Messenger().post({
            message: 'Your subscribed!!',
            type: 'success',
            showCloseButton: true
        });

        }
        // $('#add_emission_result').append("<div>Journey Added!</div>");
    });
    });



    // =====================================================

    $('#suggest_nearby_stops').click(function() {
        Messenger().run({
            action: navigator.geolocation.getCurrentPosition(success, error),
            successMessage: 'Successfully located your position!',
            errorMessage: 'an error happened ...',
            progressMessage: 'Locating your position xxx ...'
        });


        // =====================================================
        // ==== Following functions are the callbacks ==========
        // =====================================================
        function error() {
            return "Error: check your location permissions"
        }

        function success(position) {
            var user_lat = position.coords.latitude;
            var user_lng = position.coords.longitude;
            if (user_lat && user_lng) {
                $.getJSON(`apiv1/stops/${user_lng}/${user_lat}`, function(data) {
                    if ($('#start_results')) {
                        $('#start_results').html('');
                    }
                    var user_position = null;

                    var center = new google.maps.LatLng(data[0].location.coordinates[1], data[0].location.coordinates[0]);
                    $.each(data, function(key, val) {
                        //  nearest 5 stops found, add markers, drop pins on map, populate dropdown
                        var marker = new google.maps.Marker({
                            position: new google.maps.LatLng(val.location.coordinates[1], val.location.coordinates[0]),
                            map: map,
                            animation: google.maps.Animation.DROP,
                            icon: "http://labs.google.com/ridefinder/images/mm_20_green.png",
                            title: val.address
                        })
                        $('#start_results').append(`<span class="listItem">${val.stop_id} : ${val.address} ${val.stop_name}</span>`);
                    })

                    var user_position = new google.maps.Marker({
                        position: new google.maps.LatLng(user_lat, user_lng),
                        map: map,
                        optimized: false,
                        icon: "https://s22.postimg.org/a7z7pnm01/835_2.gif",
                        title: "You are here"
                    });
                    map.setCenter(center)
                    map.setZoom(16);
                })
            }
        }
    });

    // =====================================================================
    // listen for keyup event i.e typing
    // get the results of the keypress and query the database with that input
    // append the results to 'results'
    // =====================================================================
    var start_click_text,
        end_click_text;
    $('#start_position').keyup(function() {
            $('#start_results').html('');
            var query = $('#start_position').val();
            if (query) {
                $.getJSON(`/apiv1/stop/${query}`, function(data) {
                    $.each(data, function(key, val) {
                        if (val.stop_id != -1 || val.address != -1) {
                            $('#start_results').append(`<span class="listItem">${val.stop_id} : ${val.address} ${val.stop_name}</span>`);
                        }
                    })
                })
            }
        })
        // =====================================================
        // when span is clicked, store the clicked item as input
        // =====================================================
    $('#start_results').on('click', 'span', function() {
        start_click_text = $(this).text();
        // check if the different stop 
        if (end_click_text != start_click_text) {
            $('#start_position').val(start_click_text);
        } else {
            // Messenger Error
            Messenger().post({
                message: 'something is not right.',
                type: 'error',
                showCloseButton: true
            });
            $('#start_position').val('');
        }
        // clean up div
        $("#start_results").html('');
    });
    // ending stop
    // same as above
    $('#end_position').keyup(function() {
            $('#end_results').html('');
            var query = $('#end_position').val();
            if (query) {
                $.getJSON(`/apiv1/stop/${query}`, function(data) {
                    $.each(data, function(key, val) {
                        if (val.stop_id != -1 || val.address != -1) {
                            $('#end_results').append(`<span class="listItem">${val.stop_id} : ${val.address} ${val.stop_name}</span>`);
                        }
                    })
                })
            }
        })
        // when span is clicked, store the clicked item as input
    $('#end_results').on('click', 'span', function() {
        end_click_text = $(this).text();
        // check if the different stop 
        if (end_click_text != start_click_text) {
            $('#end_position').val(end_click_text);
        } else {
            // Messenger Error
            Messenger().post({
                message: 'try a different destination.',
                type: 'error',
                showCloseButton: true
            });
            $('#end_position').val('');
            return; //???????? not sure if this is working as intended
        }
        // clean up div
        $("#end_results").html('');
    });
    // ======================
    // set date picker limits
    // ======================

    // var minDate = new Date();
    // var maxDate = new Date(minDate);
    // maxDate.setDate(maxDate.getDate() + 5);

    // $('#travel_date').prop('min', minDate.toISOString().substring(0, 10));
    // $('#travel_date').prop('max', maxDate.toISOString().substring(0, 10));
    // ===========================

    // show advanced options
    $('#show_advanced_options').click(function() {
        $('#advanced').toggle(300);
    })

    // check for start point buses
    $('#send_results').click(function() {
        var origin = $('#start_position').val().split(" ");
        var start_stop_id = origin[0]
        var destination = $('#end_position').val().split(" ");
        var end_stop_id = destination[0]

        if (start_stop_id && end_stop_id) {
            var input_selected = new Date().getUnixTime();
            if ($("#arrival_time").val()) {
                var user_date = $("#arrival_time").val();
                input_selected = new Date(user_date).getUnixTime();
            }
            $.getJSON(`/apiv1/route/start/${start_stop_id}/end/${end_stop_id}/input_time/${input_selected}`, function(data) {
                $('#bus_possibility').html('')
                    // clear existing content
                if ($('#bus_to_destination')) {
                    $('#bus_to_destination').html('')
                }
                if ($('#bus_possibility')) {
                    $('#bus_possibility').html('')
                }
                if ($('#available_buses')) {
                    $('#available_buses').html('')
                }

                if (!data.length) {
                    if (data) {
                        $('#bus_possibility').append(`<h4>Your bus options</h4>`);

                        // ===================
                        var directionsDisplay = new google.maps.DirectionsRenderer({
                            polylineOptions: {
                                strokeColor: "rebeccapurple",
                                strokeWeight: 3
                            }
                        });
                        var directionsService = new google.maps.DirectionsService;
                        directionsService.route({
                            origin: {
                                lat: data.start_stop_coords[1],
                                lng: data.start_stop_coords[0]
                            },
                            destination: {
                                lat: data.end_stop_coords[1],
                                lng: data.end_stop_coords[0]
                            },
                            travelMode: google.maps.TravelMode.TRANSIT

                        }, function(response, status) {
                            if (status == 'OK') {
                                var distance = (response['routes'][0]['legs'][0]['distance']['value'] / 1000);
                                $('#distance').html(`<span>Total distance: <strong id='emission_distance'>${distance}</strong></span>`)
                                directionsDisplay.setDirections(response);
                            } else {
                                Messenger().post({
                                    message: `Directions request failed due to ${status}`,
                                    type: 'error',
                                    showCloseButton: true
                                });
                            }
                        });

                        directionsDisplay.setMap(map);
                        // live api data
                        pull_live_data(start_stop_id);
                        $('#add_emissions').html('').html(`<div>Add Journey To Emmissions</div>`);
                        $('#add_subscribe').html('').html(`<div>Create Text Subscription</div>`);
                        $('#add_subscribe_freq').html('').html(`<div id="add_subscribe_time">
                            <form action="">
                              <input type="radio" id="daily" checked name="freq" value="daily"> Daily<br>
                              <input type="radio" id="weekly" name="freq" value="weekly"> Weekly<br>
                              <input type="radio" id="workdays" name="freq" value="workdays"> Workdays
                            </form>
                    </div>`);
                        $.each(data, function(index, val) {
                            if (index !== "end_stop_coords") {
                                if (index !== "start_stop_coords") {
                                    $('#bus_possibility').append(`<span id="chosen_bus" class="bus_to_take button-small"> Accubus estimate for ${index} bus is ${Math.ceil(val)} minutes</span>`);
                                    // $('#bus_possibility').append(`<span id="chosen_bus" class="bus_to_take button-small"> Accubus estimate for ${index} bus is ${Math.ceil(val)} minutes</span>`);
                                }
                            }
                        })
                    }
                } else {
                    if ($('#bus_options')) {
                        $('#bus_options').html('')
                    }
                    $('#bus_possibility').append(`<h4>No direct buses ...</h4><div id="routing"></div>`)

                    var route_stops = []
                    $.each(data[0]['steps'], function(key, val) {
                        route_stops.push([val.route_number, val.available_journeys[0], val.available_journeys[1]])
                        $('#routing').append(`<span>${val.route_number} bus from stop ${val.available_journeys[0]} to stop ${val.available_journeys[1]}</span><br/><div class="acc_time">`)
                    })
                    $.each(route_stops, function(index, val) {
                        $.getJSON(`/apiv1/route/start/${val[1]}/end/${val[2]}/input_time/${input_selected}`, function(data) {
                            $.each(data, function(index, val) {
                                if (index == route_stops[0][0]) {
                                    total_time += Math.ceil(val[0]);
                                } else if (index == route_stops[1][0]) {
                                    total_time += Math.ceil(val[0]);
                                }
                                $('.acc_time:last').html('').html(`<span>Accubus prediction is <strong>${total_time}</strong> minutes</span>`);
                            });

                        })
                    })
                    var bounds = new google.maps.LatLngBounds();

                    var path = google.maps.geometry.encoding.decodePath(data[0].fullPolyline.points);
                    for (var i = 0; i < path.length; i++) {
                        bounds.extend(path[i]);
                    }

                    var polyline = new google.maps.Polyline({
                        path: path,
                        strokeColor: "rebeccapurple",
                        strokeWeight: 3,
                        fillColor: '#FF0000',
                        fillOpacity: 0.35,
                        map: map
                    });
                    polyline.setMap(map);
                    map.fitBounds(bounds);
                }
            })
        } else if (start_stop_id) {
            Messenger().post({
                message: "You entered an origin with no destination ...",
                type: 'info',
                showCloseButton: true
            });
            $.getJSON(`/apiv1/route/start/${start_stop_id}`, function(data) {
                if ($('#bus_to_destination')) {
                    $('#bus_to_destination').html('')
                }
                if ($('#bus_possibility')) {
                    $('#bus_possibility').html('')
                }
                if ($('#available_buses')) {
                    $('#available_buses').html('')
                }
                $('#available_buses').append(`<div id='bus_options'><h4>The following buses are available from stop : <span>${start_stop_id}</span></h4></div>`);
                pull_live_data(start_stop_id)
                $.each(data, function(index, val) {
                    $('#bus_options').append(`<span class="bus_to_take button-small">${val}</span>`);
                })
            })
        } else if (end_stop_id) {
            Messenger().post({
                message: "You entered a destination with no origin ...",
                type: 'info',
                showCloseButton: true
            });
            $.getJSON(`/apiv1/route/start/${end_stop_id}`, function(data) {
                if ($('#bus_to_destination')) {
                    $('#bus_to_destination').html('')
                }
                if ($('#bus_possibility')) {
                    $('#bus_possibility').html('')
                }
                $('#bus_to_destination').append(`<div id='bus_options'><h4>The following buses will get you there:</h4></div>`)
                $.each(data, function(index, val) {
                    $('#bus_to_destination').append(`<span class="bus_to_take button-small">${val}</span>`);
                })
            })
        } else {
            // Error Enter at least one stop ...' 
            Messenger().post({
                message: 'Enter at least one stop ...',
                type: 'error',
                showCloseButton: true
            });

        }
    })
});

// =================================================
// ========== Google Map Initialization ============
// =================================================
var map;

function initMap() {
    var dublin = {
        lat: 53.3575945,
        lng: -6.2613842
    };
    var map_options = {
        center: dublin,
        zoom: 12,
        mapTypeId: google.maps.MapTypeId.ROADMAP
    };
    var transitLayer = new google.maps.TransitLayer();
    map = new google.maps.Map(document.getElementById('map'), map_options);
    transitLayer.setMap(map);
}

// =================================================
// ==========Clear icon on search fields============
// =================================================

$(function() {
    $('.search').clearSearch({
        callback: function() {
            Messenger().post("Cleared")
        }
    });

});

(function($) {
    $.fn.clearSearch = function(options) {
        var settings = $.extend({
            'clearClass': 'clear_input',
            'focusAfterClear': true,
            'linkText': '&times;'
        }, options);
        return this.each(function() {
            var $this = $(this),
                btn,
                divClass = settings.clearClass + '_div';

            if (!$this.parent().hasClass(divClass)) {
                $this.wrap('<div style="position: relative;" class="' + divClass + '"></div>');
                $this.after('<a style="position: absolute; cursor: pointer;" class="' +
                    settings.clearClass + '">' + settings.linkText + '</a>');
            }
            btn = $this.next();

            function clearField() {
                $this.val('').change();
                triggerBtn();
                if (settings.focusAfterClear) {
                    $this.focus();
                }
                if (typeof(settings.callback) === 'function') {
                    settings.callback();
                }
            }

            function triggerBtn() {
                if (hasText()) {
                    btn.show();
                } else {
                    btn.hide();
                }
                update();
            }

            function hasText() {
                return $this.val().replace(/^\s+|\s+$/g, '').length > 0;
            }

            function update() {
                var width = $this.outerWidth(),
                    height = $this
                    .outerHeight();
                btn.css({
                    top: height / 2 - btn.height() / 2,
                    left: width - height / 2 - btn.height() / 2
                });
            }

            if ($this.prop('autofocus')) {
                $this.focus();
            }

            btn.on('click', clearField);
            $this.on('keyup keydown change focus', triggerBtn);
            triggerBtn();
        });
    };
})(jQuery);

// =============== Remove Location finder on click =============
$(document).on('click', '#suggest_nearby_stops', function() {
    $(this).remove();
});