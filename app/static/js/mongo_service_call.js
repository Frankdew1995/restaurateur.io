
const checkBtn = document.getElementById('service');

const payBtn = document.getElementById('pay');




// Service call handling
checkBtn.addEventListener("click", function(){

  const info = {};

  const tableName = document.getElementById("tableName").textContent;
  const seatNumber = document.getElementById("seatNumber").textContent;
  const isKid = document.getElementById("isKid").textContent;

  info.tableName = tableName.trim();
  info.seatNumber = seatNumber.trim();
  info.isKid = isKid.trim();

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
        window.location = `/mongo/index/${info.tableName}/${info.seatNumber}/${info.isKid}`;
      }

    } else {
      // We reached our target server, but it returned an error

    }
  };

  request.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
  request.send(data);

});



// pay call action handling
payBtn.addEventListener("click", function(){

  const info = {};

  const tableName = document.getElementById("tableName").textContent;
  const seatNumber = document.getElementById("seatNumber").textContent;

  const isKid = document.getElementById("isKid").textContent;

  info.tableName = tableName.trim();
  info.seatNumber = seatNumber.trim();
  info.isKid = isKid.trim();

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
        window.location = `/mongo/index/${info.tableName}/${info.seatNumber}/${info.isKid}`;
      }

    } else {
      // We reached our target server, but it returned an error

    }
  };

  request.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
  request.send(data);

});
