
const checkBtn = document.getElementById('checkout');

checkBtn.addEventListener("click", function(){

  const order = {};

  const productDetails = [];

  const qtyItems = document.querySelectorAll(".cd-cart__select");

  qtyItems.forEach(function(item){

    productDetails.push({'itemId': parseInt(item.children[0].id.trim()),
                          'itemQuantity': parseInt(item.children[0].value.trim())});

  });


  const tableName = document.getElementById("tableName").textContent;
  const seatNumber = document.getElementById("seatNumber").textContent;
  const isKid = document.getElementById("isKid").textContent;

  order.tableName = tableName.trim();
  order.seatNumber = seatNumber.trim();
  order.isKid = isKid.trim();

  order.details = productDetails;

  console.log(order);

  const data = JSON.stringify(order);

  var request = new XMLHttpRequest();
  request.open('POST', '/mongo/guest/checkout', true);


  request.onload = function() {
        if (this.status >= 200 && this.status < 400) {
            // Success!
            var resp = JSON.parse(this.response);
            console.log(resp);

            // if error, log the error messages
            if (resp.error){

                alert(resp.error);
                // refresh without cache
                location.reload(true);

            } else {
              // if success, alert the msg and redirect to alacarte index page

              alert(resp.success);

              // redirct handling + javascript template literals > alacarte index page
              window.location = `/mongo/index/${order.tableName}/${order.seatNumber}/${order.isKid}`;
            }

      }
      };


  request.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
  request.send(data);





});
