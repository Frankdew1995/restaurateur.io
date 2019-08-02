
// request call service status
function requestStatus(){

var request = new XMLHttpRequest();
request.open('GET', '/tables/status', true);

request.onload = function() {
  if (request.status >= 200 && request.status < 400) {
    // Success!
    var data = JSON.parse(request.responseText);

    if (data.length > 0) {

      data.forEach(function(table){

        const tableCard = document.getElementById(table);

        tableCard.style = "background-color: green";


      }
    );

    }

  } else {
    // We reached our target server, but it returned an error

  }
};

request.onerror = function() {
  // There was a connection error of some sort
};


request.send();


setTimeout(requestStatus, 15000);


};


requestStatus();










// request pay status by table
function requestPay(){

var request = new XMLHttpRequest();
request.open('GET', '/tables/pay/requested', true);

request.onload = function() {
  if (request.status >= 200 && request.status < 400) {
    // Success!
    var data = JSON.parse(request.responseText);

    if (data.length > 0) {

      data.forEach(function(table){

        const tableCard = document.getElementById(table);

        tableCard.style = "background-color: red";


      }
    );

    }

  } else {
    // We reached our target server, but it returned an error

  }
};

request.onerror = function() {
  // There was a connection error of some sort
};


request.send();


setTimeout(requestPay, 15000);


};


requestPay();
