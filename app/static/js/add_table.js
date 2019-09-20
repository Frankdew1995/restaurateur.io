
const checkBtn = document.getElementById('submit');


checkBtn.addEventListener("click", function(){

  const tableName = document.getElementById("name").value.trim();

	const persons = document.getElementById("persons").value.trim();

	const section = document.getElementById("section").value.trim();

  const info = {};

	info.tableName = tableName;
	info.persons = persons;
	info.section = section;

  console.log(info);

  const data = JSON.stringify(info);

  var request = new XMLHttpRequest();

  request.open('POST', `/js/tables/add`, true);

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
        window.location = `/adminpanel/tables/view`;
      }

    } else {
      // We reached our target server, but it returned an error

    }
  };

  request.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
  request.send(data);

});
