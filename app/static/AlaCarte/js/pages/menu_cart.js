var cartWrapper;
var productId;
var cartBody;
var cartList;
var cartTotal;
var cartTrigger;
var cartCount;
var addToCartBtn;
var undo;
var undoTimeoutId;



function toggleCart(bool) {
    var cartIsOpen = ( typeof bool === 'undefined' ) ? cartWrapper.hasClass('cart-open') : bool;

    if( cartIsOpen ) {
        cartWrapper.removeClass('cart-open');
        //reset undo
        clearInterval(undoTimeoutId);
        undo.removeClass('visible');
        cartList.find('.deleted').remove();

        setTimeout(function(){
            cartBody.scrollTop(0);
            //check if cart empty to hide it
            if( Number(cartCount.find('li').eq(0).text()) == 0) cartWrapper.addClass('empty');
        }, 500);
    } else {
        cartWrapper.addClass('cart-open');
    }
}

function addToCart(trigger) {
    //console.log(Order);

    var order=trigger[0];
    let name=order.dataset.name;
    let amount=order.dataset.amount;
    let price=order.dataset.price;
    let id=order.dataset.dishId;
    let free=true;
    //if(WATER.indexOf(findItemById(id).type)!=-1  || children==="single" ){
    if(findItemById(id).type2 ==="Water"  || children==="single"  || children==="takeout"){
        free=false;
    }
    // console.log(findItemById(id));
    if(Order.count+ parseInt(amount)>OrderLimit){
        alert(String.limit);
        return;
    }
    var cartIsEmpty = cartWrapper.hasClass('empty');
    //update cart product list

    addProduct(name,price,amount,id);
    //update number of items

    updateCartCount(cartIsEmpty,parseInt( amount));
    //update total price
    //console.log(price*amount);
    updateCartTotal(free?0:parseFloat(price)*parseFloat(amount), true);
    //show cart
    cartWrapper.removeClass('empty');
}

function addProduct(name,price,amounts,id) {
    let free=true;
    //console.log(WATER,findItemById(id));
    //if(WATER.indexOf(findItemById(id).type)!=-1 || children==="single"){
    if(findItemById(id).type2 === "Water" || children==="single"|| children==="takeout"){
        free=false;
    }
    console.log(free);
    let priceText=free?"":price+"€";
    //console.log(name,price,amounts);
    //this is just a product placeholder
    //you should insert an item with the selected product info
    //replace productId, productName, price and url with your real product info
    productId = productId + 1;
    logOrder(id,amounts,productId);
    var productAdded = '<li class="product"><div class="product-image"><a href="#0">' +
        '<img src="'+ $("#imagename").attr("src") +'" alt="placeholder"></a>' +
        '</div><div class="product-details"><h3><a href="#0">'+name+'' +
        '</a></h3><span class="price">'+priceText+'</span><div class="actions">' +
        '<a  data-id="'+id+'" data-pid="'+productId+'" href="#0" class="delete-item lan_Delete">Delete</a><div class="quantity">' +
        '<label class="lan_Amount" for="cd-product-'+ productId +'">Qty</label><span class="select">' +
        '<select id="cd-product-'+ productId +'" name="quantity">' ;
    for(var i=1;i<10;i++){
        productAdded+=  '<option value="'+i+'"' +(amounts==i?"selected":"")+'>'+i+'</option>'
    }
    productAdded+=' </select></span></div></div></div></li>';
    productAdded=$(productAdded);
    cartList.prepend(productAdded);
}

function removeProduct(product) {
    let  pid=product.find('.product').context.dataset.pid;
    removeItem(pid);
    clearInterval(undoTimeoutId);
    cartList.find('.deleted').remove();
    var topPosition = product.offset().top - cartBody.children('ul').offset().top ,
        productQuantity = Number(product.find('.quantity').find('select').val()),
        productTotPrice = Number(product.find('.price').text().replace('€', '')) * productQuantity;

    product.css('top', topPosition+'px').addClass('deleted');

    //update items count + total price
    updateCartTotal(productTotPrice, false);
    updateCartCount(true, -productQuantity);
    undo.addClass('visible');

    //wait 8sec before completely remove the item
    undoTimeoutId = setTimeout(function(){
        undo.removeClass('visible');
        cartList.find('.deleted').remove();
    }, 8000);
}

function quickUpdateCart() {
    var quantity = 0;
    var price = 0;

    cartList.children('li:not(.deleted)').each(function(){
        // let id=this.context.dataset.id;
        pid=this.children[1].children[2].children[0].dataset.pid;

        //  console.log($(this).find('select'));
        let singleQuantity = Number($(this).find('select').val());
        findItemByPId(pid).amount=singleQuantity;
        quantity = quantity + singleQuantity;

        // console.log($(this).find('select').val());
        price = price + singleQuantity*Number($(this).find('.price').text().replace('€', ''));

    });
    Order.count=quantity;
    Order.price=price;
    console.log(Order);
    cartTotal.text(price.toFixed(2));
    cartCount.find('li').eq(0).text(quantity);
    cartCount.find('li').eq(1).text(quantity+1);
}

function updateCartCount(emptyCart, quantity) {

    if( typeof quantity === 'undefined' ) {
        var actual =  Number(cartCount.find('li').eq(0).text()) + 1;
        console.log(actual);
        var next = actual + quantity;

        if( emptyCart ) {
            cartCount.find('li').eq(0).text(actual);
            cartCount.find('li').eq(1).text(next);
        } else {
            cartCount.addClass('update-count');

            setTimeout(function() {
                cartCount.find('li').eq(0).text(actual);
            }, 150);

            setTimeout(function() {
                cartCount.removeClass('update-count');
            }, 200);

            setTimeout(function() {
                cartCount.find('li').eq(1).text(next);
            }, 230);
        }
    } else {
        var actual = Number(cartCount.find('li').eq(0).text()) + quantity;
        var next = actual + 1;

        cartCount.find('li').eq(0).text(actual);
        cartCount.find('li').eq(1).text(next);
    }
}

function updateCartTotal(price, bool) {
    console.log(price,bool);
    if(price==0){
        console.log(true);
        document.getElementById("eurUnit").style.display="none";
        cartTotal.text("");
        return;
    }

    document.getElementById("eurUnit").style.display="";

    bool ? cartTotal.text( (Number(cartTotal.text()) + price).toFixed(2) )  : cartTotal.text(  (Number(cartTotal.text()) - price).toFixed(2) );
}