
// var nextTimeText = document.getElementById("nextClock").textContent;
//
// var nextRoundTime = new Date(nextTimeText);

// clock + timeDelta calculation
function startTime() {

    var now = new Date();
    document.getElementById('datetime').textContent = now.getHours() + ":" + now.getMinutes() + ":" +now.getSeconds();

  }

  
window.onload = function(){

  function startTime() {
              var now = new Date();
              document.getElementById('datetime').innerHTML = now.getHours() + ":" + now.getMinutes() + ":" +now.getSeconds();
      }

  function startInterval() {
      setInterval("startTime();",1000);
  }

  startInterval();


}
