
const checkBtn = document.getElementById('checkout');



checkBtn.addEventListener("click", function(){


  alert("Ihre Bestellung ist an die Kueche gesendet!");


  const totalPrice = parseFloat(document.getElementById("priceTotal").textContent);

  const order = {};

  order.totalPrice = totalPrice;

  const productDetails = [];

  const qtyItems = document.querySelectorAll(".cd-cart__select");

  qtyItems.forEach(function(item){

    productDetails.push({'itemId': parseInt(item.children[0].id.trim()),
                          'itemQuantity': parseInt(item.children[0].value.trim())});

  });



  const tableName = document.getElementById("tableName").textContent;
  const seatNumber = document.getElementById("seatNumber").textContent;

  order.tableName = tableName.trim();
  order.seatNumber = seatNumber.trim();

  order.details = productDetails;

  console.log(order);

  const data = JSON.stringify(order);

  var request = new XMLHttpRequest();
  request.open('POST', '/takeout/checkout', true);
  request.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
  request.send(data);





});
