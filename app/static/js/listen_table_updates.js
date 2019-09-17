

Pusher.logToConsole = true;

var pusher = new Pusher('eacdbb9eee6d56fc20b6', {
  cluster: 'eu',
  forceTLS: true
});

var channel = pusher.subscribe('orders');

// listen new inhouse orders
channel.bind('new order', function(data) {

  const tableName = document.getElementById("tableName").textContent.trim();

  if (data.success && data.table === tableName){
    location.reload(true);
  }
});
