// show cart
function showCart(){
  const cartInfo = document.getElementById('cart-info');
  const cart = document.getElementById("cart");

  cartInfo.addEventListener("click", function(){

    cart.classList.toggle("show-cart");
});
};

showCart();


// Add items to cart
function add_items(){
const cartBtn = document.querySelectorAll(".add-item-icon");

cartBtn.forEach(function(btn){

  btn.addEventListener("click", function(event){

    if (event.target.parentElement.classList.contains("add-item-icon")){


      alert("Bestaetigen?");


      const quantity = parseInt(event.target.parentElement.previousElementSibling.children[1].value);

      const name = event.target.parentElement.previousElementSibling.previousElementSibling.children[0].textContent;

      const item = {};

      item.name = name;
      item.quantity = quantity;


      let price = event.target.parentElement.previousElementSibling.previousElementSibling.children[1].textContent;

      let finalPrice = parseFloat(price.slice(1).trim())*item.quantity;

      item.price = finalPrice;
      console.log(item);

      const cartItem = document.createElement("div");

      cartItem.classList.add("cart-item", "d-flex", "justify-content-between", "text-capitalize", "my-3");

      cartItem.innerHTML = `
      <img src="${item.img}" class="img-fluid rounded-circle" id="item-img" alt="">
      <div class="item-text">

        <p id="cart-item-title" class="font-weight-bold mb-0">
          <span>
              ${item.name}
          </span>
            x
          <span>
            ${item.quantity}
          </span>

        </p>
        <span>€</span>
        <span id="cart-item-price" class="cart-item-price" class="mb-0">${item.price}</span>
      </div>
      <a href="#" id='cart-item-remove' class="cart-item-remove">
        <i class="fas fa-trash"></i>
      </a>`;


      // Select cart
      const cart = document.getElementById("cart");
      const total = document.querySelector(".cart-total-container");

      // Insert the new Item before the total price
      cart.insertBefore(cartItem, total);
      showTotals();
    }});
});

function showTotals(){

  const total = [];
  const priceItems = document.querySelectorAll(".cart-item-price");

  priceItems.forEach(function(item){
    total.push(parseFloat(item.textContent));
  });


  const finalTotal = total.reduce(function(total, item){

    total += item;
    return total
  }, 0);

  const finalSum = finalTotal.toFixed(2);

  console.log(finalSum);


  // insert value and Quantity into total
  document.getElementById('cart-total').textContent = finalSum;
  document.getElementById('item-count').textContent = total.length;
  document.querySelector('.item-total').textContent = finalSum;


};


};

// Run the add function
add_items();
