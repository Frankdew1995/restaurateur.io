
const checkBtn = document.getElementById('checkout');



checkBtn.addEventListener("click", function(){


  alert("Ihre Bestellung ist an die Kueche gesendet!");


  const totalPrice = parseFloat(document.getElementById("cart-total").textContent);

  const order = {};

  order.totalPrice = totalPrice;

  const productDetails = [];

  const itemDivs = document.querySelectorAll(".item-text");

  itemDivs.forEach(function(item){

    productDetails.push({'itemName': item.children[0].children[0].textContent.trim(),
                          'itemQuantity': item.children[0].children[1].textContent.trim()});

  });



  const tableName = document.getElementById("tableName").textContent;
  const seatNumber = document.getElementById("seatNumber").textContent;

  order.tableName = tableName.trim();
  order.seatNumber = seatNumber.trim();

  order.details = productDetails;

  console.log(order);

  const data = JSON.stringify(order);

  var request = new XMLHttpRequest();
  request.open('POST', '/alacarte/guest/checkout', true);
  request.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8');
  request.send(data);





});
