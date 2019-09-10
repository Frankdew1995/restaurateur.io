
var nextTimeText = document.getElementById("nextClock").textContent;

var nextRoundTime = new Date(nextTimeText);

// clock + timeDelta calculation
function startTime() {

    var now = new Date();
    document.getElementById('datetime').textContent = now.getHours() + ":" + now.getMinutes() + ":" +now.getSeconds();

  }

  // Set the date we're counting down to
  var countDownDate = nextRoundTime.getTime();

  // Update the count down every 1 second
  var x = setInterval(function() {

    // Get today's date and time
    var now = new Date().getTime();

    // Find the distance between now and the count down date
    var distance = countDownDate - now;

    // Time calculations for days, hours, minutes and seconds
    var days = Math.floor(distance / (1000 * 60 * 60 * 24));
    var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
    var seconds = Math.floor((distance % (1000 * 60)) / 1000);

    // Output the result in an element with id="demo"
    document.getElementById("timedelta").textContent = minutes + ":" + seconds;

    // If the count down is over, write some text
    if (distance < 0) {
      clearInterval(x);
      document.getElementById("timedelta").textContent = "Die nächste Runde steht für Sie bereit";
    }
  }, 1000);

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
