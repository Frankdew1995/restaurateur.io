
const checkBtn = document.getElementById('service');


const payKarte = document.getElementById('Karte');

const payBar = document.getElementById('Bar');



// Service call handling
checkBtn.addEventListener("click", function(){

  const info = {};

  const tableName = document.getElementById("tableName").textContent;
  const seatNumber = document.getElementById("seatNumber").textContent;

  info.tableName = tableName.trim();
  info.seatNumber = seatNumber.trim();

  console.log(info);

  const data = JSON.stringify(info);

  var request = new XMLHttpRequest();
  request.open('POST', '/service/call', true);

  request.onload = function() {
  if (this.status >= 200 && this.status < 400) {
      // Success!
      var resp = JSON.parse(this.response);
      console.log(resp);

      // if error, log the error messages
      if (resp.error){

          alert(resp.error);

      } else {
        // if success, alert the msg and redirect to jp buffet index page
        alert(resp.success);

        // redirct handling + javascript template literals
        window.location = `/alacarte/interface/${info.tableName}/${info.seatNumber}`;
      }

    } else {
      // We reached our target server, but it returned an error

    }
  };

  request.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
  request.send(data);

});



// pay with Cash
payBar.addEventListener("click", function(){

  const info = {};

  const tableName = document.getElementById("tableName").textContent;
  const seatNumber = document.getElementById("seatNumber").textContent;

  const payWith = payBar.id.trim();

  info.tableName = tableName.trim();
  info.seatNumber = seatNumber.trim();
  info.payWith = payWith;


  console.log(info);

  const data = JSON.stringify(info);

  var request = new XMLHttpRequest();
  request.open('POST', '/pay/call', true);

  request.onload = function() {
  if (this.status >= 200 && this.status < 400) {
      // Success!
      var resp = JSON.parse(this.response);
      console.log(resp);

      // if error, log the error messages
      if (resp.error){

          alert(resp.error);

      } else {
        // if success, alert the msg and redirect to jp buffet index page
        alert(resp.success);

        // redirct handling + javascript template literals
        window.location = `/alacarte/interface/${info.tableName}/${info.seatNumber}`;
      }

    } else {
      // We reached our target server, but it returned an error

    }
  };

  request.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
  request.send(data);

});



// pay with card
payKarte.addEventListener("click", function(){

  const info = {};

  const tableName = document.getElementById("tableName").textContent;
  const seatNumber = document.getElementById("seatNumber").textContent;

  const payWith = payKarte.id.trim();

  info.tableName = tableName.trim();
  info.seatNumber = seatNumber.trim();
  info.payWith = payWith;

  console.log(info);

  const data = JSON.stringify(info);

  var request = new XMLHttpRequest();
  request.open('POST', '/pay/call', true);

  request.onload = function() {
  if (this.status >= 200 && this.status < 400) {
      // Success!
      var resp = JSON.parse(this.response);
      console.log(resp);

      // if error, log the error messages
      if (resp.error){

          alert(resp.error);

      } else {
        // if success, alert the msg and redirect to jp buffet index page
        alert(resp.success);

        // redirct handling + javascript template literals
        window.location = `/alacarte/interface/${info.tableName}/${info.seatNumber}`;
      }

    } else {
      // We reached our target server, but it returned an error

    }
  };

  request.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
  request.send(data);

});
