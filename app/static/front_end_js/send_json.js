
const checkBtn = document.getElementById('checkout');





checkBtn.addEventListener("click", function(){


  const totalPrice = document.getElementById("cart-total").textContent

  const order = {'totalPrice': totalPrice
                  };

  const productDetails = []

  const itemDivs = document.querySelectorAll(".item-text");

  itemDivs.forEach(function(item){

    productDetails.push({'itemName': item.children[0].textContent,
                          'itemPrice': item.children[2].textContent});

  });

  console.log(productDetails);

  order.details = productDetails;

  const data = JSON.stringify(order);

  var request = new XMLHttpRequest();
  request.open('POST', '/takeout/checkout', true);
  request.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8');
  request.send(data);





});
