(function(){
  // Add to Cart Interaction - by CodyHouse.co
  var cart = document.getElementsByClassName('js-cd-cart');
  if(cart.length > 0) {
  	var cartAddBtns = document.getElementsByClassName('add-item-icon'),
  		cartBody = cart[0].getElementsByClassName('cd-cart__body')[0],
  		cartList = cartBody.getElementsByTagName('ul')[0],
  		cartListItems = cartList.getElementsByClassName('cd-cart__product'),
  		cartTotal = cart[0].getElementsByClassName('cd-cart__checkout')[0].getElementsByTagName('span')[0],
  		cartCount = cart[0].getElementsByClassName('cd-cart__count')[0],
  		cartCountItems = cartCount.getElementsByTagName('li'),
  		cartUndo = cart[0].getElementsByClassName('cd-cart__undo')[0],
  		productId = 0, //this is a placeholder -> use your real product ids instead
  		cartTimeoutId = false,
  		animatingQuantity = false;
		initCartEvents();


		function initCartEvents() {
			// add products to cart
			for(var i = 0; i < cartAddBtns.length; i++) {(function(i){
				cartAddBtns[i].addEventListener('click', addToCart);
			})(i);}

			// open/close cart
			cart[0].getElementsByClassName('cd-cart__trigger')[0].addEventListener('click', function(event){
				event.preventDefault();
				toggleCart();
			});

			cart[0].addEventListener('click', function(event) {
				if(event.target == cart[0]) { // close cart when clicking on bg layer
					toggleCart(true);
				} else if (event.target.closest('.cd-cart__delete-item')) { // remove product from cart
					event.preventDefault();
					removeProduct(event.target.closest('.cd-cart__product'));
				}
			});

			// update product quantity inside cart
			cart[0].addEventListener('change', function(event) {
				if(event.target.tagName.toLowerCase() == 'select') quickUpdateCart();
			});

			//reinsert product deleted from the cart
			cartUndo.addEventListener('click', function(event) {
				if(event.target.tagName.toLowerCase() == 'a') {
					event.preventDefault();
					if(cartTimeoutId) clearInterval(cartTimeoutId);
					// reinsert deleted product
					var deletedProduct = cartList.getElementsByClassName('cd-cart__product--deleted')[0];
					Util.addClass(deletedProduct, 'cd-cart__product--undo');
					deletedProduct.addEventListener('animationend', function cb(){
						deletedProduct.removeEventListener('animationend', cb);
						Util.removeClass(deletedProduct, 'cd-cart__product--deleted cd-cart__product--undo');
						deletedProduct.removeAttribute('style');
						quickUpdateCart();
					});
					Util.removeClass(cartUndo, 'cd-cart__undo--visible');
				}
			});
		};

		function addToCart(event) {
			event.preventDefault();
			if(animatingQuantity) return;
			var cartIsEmpty = Util.hasClass(cart[0], 'cd-cart--empty');
			//update cart product list
			addProduct(this);
			//update number of items
			updateCartCount(cartIsEmpty);
			//update total price
			// updateCartTotal(this.getAttribute('data-price'), true);
			//show cart
			Util.removeClass(cart[0], 'cd-cart--empty');
		};

		function toggleCart(bool) { // toggle cart visibility
			var cartIsOpen = ( typeof bool === 'undefined' ) ? Util.hasClass(cart[0], 'cd-cart--open') : bool;

			if( cartIsOpen ) {
				Util.removeClass(cart[0], 'cd-cart--open');
				//reset undo
				if(cartTimeoutId) clearInterval(cartTimeoutId);
				Util.removeClass(cartUndo, 'cd-cart__undo--visible');
				removePreviousProduct(); // if a product was deleted, remove it definitively from the cart

				setTimeout(function(){
					cartBody.scrollTop = 0;
					//check if cart empty to hide it
					if( Number(cartCountItems[0].innerText) == 0) Util.addClass(cart[0], 'cd-cart--empty');
				}, 500);
			} else {
				Util.addClass(cart[0], 'cd-cart--open');
			}
		};

		function addProduct(target) {
			// this is just a product placeholder
			// you should insert an item with the selected product info
			// replace productId, productName, price and url with your real product info
			// you should also check if the product was already in the cart -> if it is, just update the quantity

        const quantity = parseInt(event.target.parentElement.previousElementSibling.children[1].value);
        const productName = event.target.parentElement.previousElementSibling.previousElementSibling.children[0].textContent;

        const image = event.target.parentElement.parentElement.previousElementSibling.children[0].src;
        const price = parseFloat(event.target.parentElement.previousElementSibling.previousElementSibling.children[1].textContent.replace("€", "").trim());

        const productId = parseInt(event.target.parentElement.id);

        console.log(typeof(quantity), productName, image, price, productId);


        function isSelected(value){

          return (value === quantity?`<option value=${value} selected>${value}</option>`:`<option value=${value}>${value}</option>`);


        };


        var productAdded = `
                <li class="cd-cart__product">
                    <div class="cd-cart__image">
                        <a href="#0">
                            <img src="${image}" alt="placeholder">
                        </a>
                    </div>
                <div class="cd-cart__details">
                  <h3 class="truncate">
                    <a href="#0">
                      ${productName}
                    </a>
                  </h3>
                  <span class="cd-cart__price">${"€" + (price * quantity).toLocaleString('de-DE') + ",00"}</span>
                  <div class="cd-cart__actions">
                    <a href="#0" class="cd-cart__delete-item">
                      Delete
                    </a>
                    <div class="cd-cart__quantity">
                      <label for="${productId}">
                        Qty
                      </label>
                      <span class="cd-cart__select">
                        <select class="reset" id="${productId}" name="quantity">`+
                          isSelected(value=1) +
                          isSelected(value=2) +
                          isSelected(value=3) +
                          isSelected(value=4) +
                          isSelected(value=5) +
                          isSelected(value=6) +
                          isSelected(value=7) +
                          isSelected(value=8) +
                          isSelected(value=9) +
                        `</select>

                      </span>
                    </div>
                  </div>
                </div>
              </li>`;

			cartList.insertAdjacentHTML('beforeend', productAdded);


      const priceItems = document.querySelectorAll('.cd-cart__price');
      const total = [];

      priceItems.forEach(function(item){
        total.push(parseFloat(item.textContent.replace("€", "").trim()));
      });

      const finalTotal = total.reduce(function(total, item){

        total += item;
        return total
      }, 0);


      const totalPrice = document.getElementById('priceTotal');

      totalPrice.textContent = finalTotal.toLocaleString('de-DE') + ",00";



      const qties = [];
      const quantItems = document.querySelectorAll(".cd-cart__select");

      quantItems.forEach(function(item){

        qties.push(parseInt(item.children[0].value))

      });

      const totalQuantity = qties.reduce(function(total, item){

        total += item;
        return total
      }, 0);



      // select quantity displayer

      const qtyDisplayer1 = document.getElementById('qtyDisplayer1');
      const qtyDisplayer2 = document.getElementById('qtyDisplayer2');


      qtyDisplayer1.textContent = totalQuantity;
      qtyDisplayer2.textContent = totalQuantity;


		};

		function removeProduct(product) {
			if(cartTimeoutId) clearInterval(cartTimeoutId);
			removePreviousProduct(); // prduct previously deleted -> definitively remove it from the cart

			var topPosition = product.offsetTop,
				productQuantity = Number(product.getElementsByTagName('select')[0].value),
				productTotPrice = Number((product.getElementsByClassName('cd-cart__price')[0].innerText).replace('€', '')) * productQuantity;

			product.style.top = topPosition+'px';
			Util.addClass(product, 'cd-cart__product--deleted');

			//update items count + total price
			// updateCartTotal(productTotPrice, false);
			updateCartCount(true, -productQuantity);
			Util.addClass(cartUndo, 'cd-cart__undo--visible');

			//wait 8sec before completely remove the item
			cartTimeoutId = setTimeout(function(){
				Util.removeClass(cartUndo, 'cd-cart__undo--visible');
				removePreviousProduct();
			}, 8000);
		};

		function removePreviousProduct() { // definitively removed a product from the cart (undo not possible anymore)
			var deletedProduct = cartList.getElementsByClassName('cd-cart__product--deleted');
			if(deletedProduct.length > 0 ) deletedProduct[0].remove();
		};

		function updateCartCount(emptyCart, quantity) {
			if( typeof quantity === 'undefined' ) {
				var actual = Number(cartCountItems[0].innerText);
				var next = actual;

				if( emptyCart ) {
					cartCountItems[0].innerText = actual;
					cartCountItems[1].innerText = next;
					animatingQuantity = false;
				} else {
					Util.addClass(cartCount, 'cd-cart__count--update');

					setTimeout(function() {
						cartCountItems[0].innerText = actual;
					}, 150);

					setTimeout(function() {
						Util.removeClass(cartCount, 'cd-cart__count--update');
					}, 200);

					setTimeout(function() {
						cartCountItems[1].innerText = next;
						animatingQuantity = false;
					}, 230);
				}
			} else {
				var actual = Number(cartCountItems[0].innerText) + quantity;
				var next = actual;

				cartCountItems[0].innerText = actual;
				cartCountItems[1].innerText = next;
				animatingQuantity = false;
			}
		};

		function updateCartTotal(price, bool) {
			cartTotal.innerText = bool ? (Number(cartTotal.innerText) + Number(price)).toFixed(2) : (Number(cartTotal.innerText) - Number(price)).toFixed(2);
		};

		function quickUpdateCart() {
			var quantity = 0;
			var price = 0;

			for(var i = 0; i < cartListItems.length; i++) {
				if( !Util.hasClass(cartListItems[i], 'cd-cart__product--deleted') ) {
					var singleQuantity = Number(cartListItems[i].getElementsByTagName('select')[0].value);
					quantity = quantity + singleQuantity;
					price = price + singleQuantity*Number((cartListItems[i].getElementsByClassName('cd-cart__price')[0].innerText).replace('$', ''));
				}
			}

			cartTotal.innerText = price.toFixed(2);
			cartCountItems[0].innerText = quantity;
			cartCountItems[1].innerText = quantity+1;
		};
  }
})();
