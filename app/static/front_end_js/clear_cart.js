// clear cart


var clearBtn = document.getElementById('clear-cart');


clearBtn.addEventListener("click", function(){

const cartItems = document.getElementsByClassName("cart-item d-flex justify-content-between text-capitalize my-3");

console.log(cartItems);

for (var i = 0; i < cartItems.length; ++i) {
  cartItems[i].remove();
}

});
