
$(document).ready(function(){


  $("#checkout").on('click', function(){

    var totalPrice = $("#cart-total").text();

    const orderID = document.getElementById("orderID").textContent;


    console.log(totalPrice);

    const order = {'totalPrice': totalPrice,
                    'orderID': orderID
                      };

    const productDetails = {};

    const itemDivs = document.querySelectorAll(".product");

    itemDivs.forEach(function(item){


      var keyName = item.children[1].children[0].textContent;

      productDetails[keyName] = {'price': item.children[2].textContent,
                          'quantity':item.children[3].children[0].value}

    });

    console.log(productDetails);


    order.details = productDetails;

    console.log(order);

    const data = JSON.stringify(order);

    console.log(data);

    req = $.ajax({
      url:'/order/update',
      type: 'POST',
      data: data,
      contentType: 'application/json;charset=UTF-8'
    });




  });


});
