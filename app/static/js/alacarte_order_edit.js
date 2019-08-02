/* Set rates + misc */

var fadeTime = 300;


/* Assign actions */
$('.product-quantity input').change( function() {
  updateQuantity(this);
});

$('.product-removal button').click( function() {
  removeItem(this);
});

/* Update quantity */
function updateQuantity(quantityInput)
{
  /* Calculate line price */
  var productRow = $(quantityInput).parent().parent();
  var price = parseFloat(productRow.children('.product-price').text());
  var quantity = $(quantityInput).val();
  var linePrice = price * quantity;

  /* Update line price display and recalc cart totals */
  productRow.children('.product-line-price').each(function () {
    $(this).fadeOut(fadeTime, function() {
      $(this).text(linePrice.toFixed(2));
      recalculateCart();
      $(this).fadeIn(fadeTime);
    });
  });
}

/* Remove item from cart */
function removeItem(removeButton)
{
  /* Remove row from DOM and recalc cart total */
  var productRow = $(removeButton).parent().parent();
  productRow.slideUp(fadeTime, function() {
    productRow.remove();
    recalculateCart();
  });
}



const confirmBtn = document.getElementById('update');


const orderId = parseInt(document.getElementById('orderId').textContent.trim());



confirmBtn.addEventListener("click", function(){


  alert("确定更改吗？");

  console.log(orderId);


  const order = {};

  order.orderId = orderId;

  const productDetails = [];


  const products = document.querySelectorAll(".product");



  products.forEach(function(item){

    productDetails.push({
            "item": item.children[0].children[0].textContent.trim(),
            "quantity": item.children[2].children[0].value

          });



  });

  order.details = productDetails;

  console.log(productDetails);


  const data = JSON.stringify(order);

  console.log(data);

  var request = new XMLHttpRequest();
  request.open('POST', '/alacarte/orders/update', true);
  request.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8');
  request.send(data);



});
