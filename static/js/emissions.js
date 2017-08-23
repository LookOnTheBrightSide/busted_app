function band_to_c02(band) { // Declare a function
  switch(band) {
    case 'a0':
        c02 = 0;
        break;
    case 'a1':
        c02 = 80;
        break;
    case 'a2':
        c02 = 100;
        break;    
    case 'a3':
        c02 = 110;
        break;
    case 'a4':
        c02 = 120;
        break;
    case 'b1':
        c02 = 130;
        break;
    case 'b2':
        c02 = 140;
        break;
    case 'c':
        c02 = 155;
        break;
    case 'd':
        c02 = 170;
        break;
    case 'e':
        c02 = 190;
        break;
    case 'f':
        c02 = 225;
        break;        
    default:
        c02 = 250;
  }
  return c02
};

function band_to_tax(band) { // Declare a function
  switch(band) {
    case 'a0':
        tax_amount = 1230
        break;
    case 'a1':
        tax_amount = 170
        break;
    case 'a2':
        tax_amount = 180
        break;    
    case 'a3':
        tax_amount = 190
        break;
    case 'a4':
        tax_amount = 200
        break;
    case 'b1':
        tax_amount = 270
        break;
    case 'b2':
        tax_amount = 280
        break;
    case 'c':
        tax_amount = 390
        break;
    case 'd':
        tax_amount = 570
        break;
    case 'e':
        tax_amount = 750
        break;
    case 'f':
        tax_amount = 1200
        break;        
    default:
        tax_amount = 2350
  }
  return tax_amount
};

$(document).ready(function () {

  var login_name = document.getElementById('login_name');
  var login_pic = document.getElementById('login_pic');
  var last_login = document.getElementById('last_login');
  login_name.innerHTML = "";
  login_pic.innerHTML = "";
  last_login.innerHTML = "";

  $.get(`/user_data`, function(data){
    var obj = JSON.parse(data);
    if(obj.last_login.length != 1){
      
    // get the second last login, eg the last time you were here.
    var timestamp = obj.last_login[obj.last_login.length - 2],
    date = new Date(timestamp * 1000),
    datevalues = [
       date.getFullYear(),
       date.getMonth()+1,
       date.getDate(),
       date.getHours(),
       date.getMinutes(),
       date.getSeconds(),
    ];
    
    login_name.innerHTML += (obj.name);
    last_login.innerHTML += ("Last Login: " + datevalues[2] + "-" + datevalues[1] + "-" + datevalues[0]);
    login_pic.innerHTML += ("<img src='https://graph.facebook.com/" + obj._id + "/picture?type=square'>");
  }else{
    login_name.innerHTML += (obj.name);
    login_pic.innerHTML += ("<img src='https://graph.facebook.com/" + obj._id + "/picture?type=square'>");
  }
  });

$.getJSON(`/get_journey/`, function(data) {
  car_emissions = 0
  bus_emissions = 0

  if(data.journey.hasOwnProperty('journey')){
    for(i = 0; i < data.journey.journey.length; i++){
      distance = Math.min((data.journey.journey[i][2]), (data.journey.journey[i][1]));
      bus_emissions += Number(distance) * 77
      car_emissions += Number(distance) * band_to_c02(data.journey.journey[i][0])
    }
      $('.counter').each(function() {
      var $this = $(this),
          countTo = car_emissions - bus_emissions;
      
      $({ countNum: $this.text()}).animate({
        countNum: countTo
      },

      {
        duration: 3000,
        easing:'linear',
        step: function() {
          $this.text(Math.round(this.countNum));
        },
        complete: function() {
          $this.text(Math.round(this.countNum));
        }

      }); 
    });
    } else {
      $('.counter').html("Enter some journeys and this page will track them!")
      $('#saved_info').html('')
      console.log("no data to present")
    };
  });

  google.charts.load('current', {'packages':['corechart']});
  google.charts.setOnLoadCallback(drawChart);


  function drawChart() {
    
    $.getJSON(`/get_journey/`, function(data) {
    table = []
    row = []
    if(data.journey.hasOwnProperty('journey')){
      fuel = data.fuel_price
      bus_cost = 2.50
      tax_cost = band_to_tax(data.journey.car_tax)
      co2 = band_to_c02(data.journey.car_tax)
      l_1_km = co2 * 0.043103448275862/100
      yr_car = ((tax_cost + parseInt(data.journey.insurance)) / 261)
      for(i = 0; i < data.journey.journey.length; i++){
        distance = Math.min((data.journey.journey[i][2]), (data.journey.journey[i][1]));
        cost_for_trip = (((distance * l_1_km) * fuel)/100) + yr_car
        row = []
        row.push(i+1)
        row.push(Number(distance) * 77);
        row.push("<div>Bus CO2 Emissions are " + (Number(distance * 77).toString()) + " grams.</div> The money saved by getting the bus instead of driving is €"+ (+((cost_for_trip - bus_cost).toFixed(2))) +"</div>")
        row.push(Number(distance) * band_to_c02(data.journey.journey[i][0]));
        row.push("<div>Car CO2 Emissions are " + (Number(distance) * band_to_c02(data.journey.journey[i][0])) + " grams </div> <div>Car tax band: " + data.journey.journey[i][0] + "</div> <div>The cost of petrol for this trip is €" + (+((((distance * l_1_km) * fuel)/100).toFixed(2))) +  "</div>")
        table.push(row);
      }

    var dataTable = new google.visualization.DataTable();
    // var dataTable = new google.visualization.DataTable();
    // dataTable.addColumn('string', 'Country');
    // // Use custom HTML content for the domain tooltip.
    dataTable.addColumn('number', 'Journey');
    dataTable.addColumn('number', 'Bus CO2');
    dataTable.addColumn({type: 'string', role: 'tooltip', 'p': {'html': true}});
    dataTable.addColumn('number', 'Car CO2');
    dataTable.addColumn({type: 'string', role: 'tooltip', 'p': {'html': true}});
    dataTable.addRows(table);

    var options = {
      title: 'Emissions Data Per Journey',
      curveType: 'none',
      tooltip: {isHtml: true},
      legend: { position: 'bottom' },
      'width': 500,
      'height': 400
    };


    var chart = new google.visualization.AreaChart(document.getElementById('curve_chart'));

    chart.draw(dataTable, options);

    } else {
      console.log("no data either, ")
    }

    })
  };


  function myFunction() {
      var insurance = document.getElementById("myNumber").value;
      document.getElementById("demo").innerHTML = insurance;
  }

  // send the recorded route.
  $('#send_route').click(function () {
    var route_val = $('#route').val();
    var distance_val = $('#distance').val();
    $.getJSON(`/add_route_data/${route_val}/${distance_val}`, function(data) {
      $('#result').html(data);
    });
  });

  // send the tax info.
  $('#send_tax').click(function () {
    var tax_val = $('#tax').val();
    var insurance = $('#insurance').val();
    var phone = $('#phone_number').val();
    $.getJSON(`/add_car_tax/${tax_val}/${insurance}/${phone}`, function(data) {
      $('#result').html(data);
    });
  });
});

