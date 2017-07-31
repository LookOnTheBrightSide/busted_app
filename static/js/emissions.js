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

$(document).ready(function () {

  var login_name = document.getElementById('login_name');
  var login_pic = document.getElementById('login_pic');
  var last_login = document.getElementById('last_login');
  login_name.innerHTML = "";
  login_pic.innerHTML = "";
  last_login.innerHTML = "";

  $.get("http://localhost:8080/user_data", function(data){
    var obj = JSON.parse(data);
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
    login_pic.innerHTML += ("<img src='http://graph.facebook.com/" + obj._id + "/picture?type=square'>");

  });

$.getJSON(`/get_journey/`, function(data) {
  car_emissions = 0
  bus_emissions = 0

  // console.log(data.journey.journey.journey);

  for(i = 0; i < data.journey.journey.length; i++){
    bus_emissions += Number(data.journey.journey[i][2]) * 77
    car_emissions += Number(data.journey.journey[i][2]) * band_to_c02(data.journey.journey[i][0])
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
        $this.text(Math.floor(this.countNum));
      },
      complete: function() {
        $this.text(this.countNum);
      }

    }); 
  });
  });

  google.charts.load('current', {'packages':['corechart']});
  google.charts.setOnLoadCallback(drawChart);

  function drawChart() {
    
    $.getJSON(`/get_journey/`, function(data) {

    table = []
    row = []
    for(i = 0; i < data.journey.journey.length; i++){
      row = []
      row.push(i+1)
      row.push(Number(data.journey.journey[i][2]) * 77);
      row.push("<div>Bus CO2 Emissions: " + (Number(data.journey.journey[i][2]) * 77).toString() + " grams.</div>")
      row.push(Number(data.journey.journey[i][2]) * band_to_c02(data.journey.journey[i][0]));
      row.push("<div>Car CO2 Emissions: " + (Number(data.journey.journey[i][2]) * band_to_c02(data.journey.journey[i][0])) + " grams.</div><div>Car tax band: " + data.journey.journey[i][0] + "</div>")
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
      legend: { position: 'bottom' }
    };

    var chart = new google.visualization.AreaChart(document.getElementById('curve_chart'));

    chart.draw(dataTable, options);

    })
  };

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
    $.getJSON(`/add_car_tax/${tax_val}`, function(data) {
      $('#result').html(data);
    });
  });
});