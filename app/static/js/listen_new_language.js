// listen to language setting event
Pusher.logToConsole = true;

var pusher = new Pusher('eacdbb9eee6d56fc20b6', {
  cluster: 'eu',
  forceTLS: true
});

var channel = pusher.subscribe('filechange');

// listen new inhouse orders
channel.bind('newlanguage', function(data) {
  // reload the page to load the new lan settings
  console.log("hey");
  location.reload(true);

});
