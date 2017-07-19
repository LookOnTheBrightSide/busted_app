$(document).ready(function () {

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


  $('#suggest_nearby_stops').click(function () {
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
        $.getJSON(`apiv1/stops/${user_lng}/${user_lat}`, function (data) {
          if ($('#start_results')) {
            $('#start_results').html('');
          }
          $.each(data, function (key, val) {
            $('#start_results').append(`<span class="listItem">${val.stop_id} : ${val.address} ${val.stop_name}</span>`);
          })
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
  $('#start_position').keyup(function () {
    $('#start_results').html('');
    var query = $('#start_position').val();
    if (query) {
      $.getJSON(`/apiv1/stop/${query}`, function (data) {
        $.each(data, function (key, val) {
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
  $('#start_results').on('click', 'span', function () {
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
  $('#end_position').keyup(function () {
    $('#end_results').html('');
    var query = $('#end_position').val();
    if (query) {
      $.getJSON(`/apiv1/stop/${query}`, function (data) {
        $.each(data, function (key, val) {
          if (val.stop_id != -1 || val.address != -1) {
            $('#end_results').append(`<span class="listItem">${val.stop_id} : ${val.address} ${val.stop_name}</span>`);
          }
        })
      })
    }
  })
  // when span is clicked, store the clicked item as input
  $('#end_results').on('click', 'span', function () {
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

  var minDate = new Date();
  var maxDate = new Date(minDate);
  maxDate.setDate(maxDate.getDate() + 5);

  $('#travel_date').prop('min', minDate.toISOString().substring(0, 10));
  $('#travel_date').prop('max', maxDate.toISOString().substring(0, 10));
  // ===========================

  // show advanced options
  $('#show_advanced_options').click(function () {
    $('#advanced').toggle(300);
  })

  // check for start point buses
  $('#send_results').click(function () {
    var origin = $('#start_position').val().split(" ");
    var start_stop_id = origin[0]
    var destination = $('#end_position').val().split(" ");
    var end_stop_id = destination[0]
    // hadling form inputs
    if (start_stop_id && end_stop_id) {
      $.getJSON(`/apiv1/route/start/${start_stop_id}/end/${end_stop_id}`, function (data) {
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
        // =======================
        if (data) {
          $('#bus_possibility').append(`<h4>Your bus options</h4>`)
          $.each(data, function (index, val) {
            $('#bus_possibility').append(`<span id="chosen_bus" class="bus_to_take button">${index} : ${Math.round(val)} minutes</span>`);
          })
        } else {
          if ($('#bus_options')) {
            $('#bus_options').html('')
          }
          $('#bus_possibility').append(`<h4>No direct buses ...</h4>`)
        }
      })
    } else if (start_stop_id) {
      Messenger().post({
        message: "You entered an origin with no destination ...",
        type: 'info',
        showCloseButton: true
      });
      $.getJSON(`/apiv1/route/start/${start_stop_id}`, function (data) {
        if ($('#bus_to_destination')) {
          $('#bus_to_destination').html('')
        }
        if ($('#bus_possibility')) {
          $('#bus_possibility').html('')
        }
        if ($('#available_buses')) {
          $('#available_buses').html('')
        }
        $('#available_buses').append(`<div id='bus_options'><h4>The following buses are available from stop : <span>${start_stop_id}</span></h4></div>`)
        $.each(data, function (index, val) {
          $('#bus_options').append(`<span class="bus_to_take button-small">${val}</span>`);
        })
      })
    } else if (end_stop_id) {
      Messenger().post({
        message: "You entered a destination with no origin ...",
        type: 'info',
        showCloseButton: true
      });
      $.getJSON(`/apiv1/route/start/${end_stop_id}`, function (data) {
        if ($('#bus_to_destination')) {
          $('#bus_to_destination').html('')
        }
        if ($('#bus_possibility')) {
          $('#bus_possibility').html('')
        }
        $('#bus_to_destination').append(`<div id='bus_options'><h4>The following buses will get you there:</h4></div>`)
        $.each(data, function (index, val) {
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

// Google Map
var map;

function initMap() {
  var dublin = {
    lat: 53.3575945,
    lng: -6.2613842
  };
  var map_options = {
    center: dublin,
    zoom: 12,
    mapTypeId: 'roadmap'
  };
  var transitLayer = new google.maps.TransitLayer();

  map = new google.maps.Map(document.getElementById('map'), map_options);
  transitLayer.setMap(map);
}