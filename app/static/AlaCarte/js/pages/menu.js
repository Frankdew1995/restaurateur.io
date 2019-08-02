//configue and initial;
let Order={};
let menuData=[];
let menuInfo=[];
let OrderLimit=999;
let type=getQueryString("type");
let sedned = false;

let waiting=false;
let CurrentRound=0;
let NextTime=new Date();
let FinalTime=new Date();//jxy
let timeOut=false;

var timestamp=new Date().getTime();


$( document ).ready(function () {
    //getRound();
    //getFinalTime();
    //getNextTime();

    cartWrapper = $('.cd-cart-container');
    //product id - you don't need a counter in your real project but you can use your real product id
    productId = 0;

    if( cartWrapper.length > 0 ) { 
        //store jQuery objects
        cartBody = cartWrapper.find('.body');
        cartList = cartBody.find('ul').eq(0);
        cartTotal = cartWrapper.find('.checkout').find('span');
        cartTrigger = cartWrapper.children('.cd-cart-trigger');
        cartCount = cartTrigger.children('.count');
        addToCartBtn = $('.cd-add-to-cart');
        undo = cartWrapper.find('.undo');
        //undoTimeoutId;//jxy

        //add product to cart
        addToCartBtn.on('click', function(event){
            event.preventDefault();
            addToCart($(this));
        });

        //open/close cart
        cartTrigger.on('click', function(event){
            event.preventDefault();
            toggleCart();
            sedned = false;
            //console.log(timestamp);
        });

        //close cart when clicking on the .cd-cart-container::before (bg layer)
        cartWrapper.on('click', function(event){
            if( $(event.target).is($(this)) ) toggleCart(true);
        });

        //delete an item from the cart
        cartList.on('click', '.delete-item', function(event){
            event.preventDefault();
            removeProduct($(event.target).parents('.product'));
        });

        //update item quantity
        cartList.on('change', 'select', function(event){
            console.log(event);
            console.log(event.target.parentElement.parentElement.parentElement.children[0].dataset);
            let target=findItemByPId(event.target.parentElement.parentElement.parentElement.children[0].dataset.pid);

            let amount=event.target.value;

            console.log(target.amount,amount,Order.count);
            console.log(Order.count+parseInt(amount)-parseInt(target.amount));
            if(parseInt(Order.count)+parseInt(amount)-parseInt(target.amount)>OrderLimit){

                alert(String.limit);
                event.target.value=parseInt(target.amount);
                return;
            }

            quickUpdateCart();
        });

        //reinsert item deleted from the cart
        undo.on('click', 'a', function(event){
            alert(undoTimeoutId)
            //clearInterval(undoTimeoutId);//jxy
            event.preventDefault();
            cartList.find('.deleted').addClass('undo-deleted').one('webkitAnimationEnd oanimationend msAnimationEnd animationend', function(){
                $(this).off('webkitAnimationEnd oanimationend msAnimationEnd animationend').removeClass('deleted undo-deleted').removeAttr('style');
                quickUpdateCart();
            });
            undo.removeClass('visible');
        });
    }

    initial();
    getMenuInfo();
    LoadBasicData();
    Order={};
    Order.tableName=getQueryString("tableName");
    Order.tableID=getQueryString("tableId");
    Order.count=0;
    Order.price=0;




});
function typeFilter() {

    //console.log(type);
    if(type==="water" || children==="single" || children=='takeout'){//jxy

    }else{
        $(".itemPrice").toggle();//jxy
        OrderLimit=MAXDISH;
    }
}
function addRound() {
    $.ajax({
        url:"../php/menuDataByXSTAR.php?q=updateCurrentRound",
        data:{
            tablenr:tableId,
            seat:seat
        },
        method:"POST",
        success:function (res) {
            console.log(res);
            if(res=="good"){
               window.location.href="index.html"+param;
            }

        }
    })
}
/*function getOrderInfo() {
    $.ajax({
        url:"../php/menuDataByXSTAR.php?q=getAllData",
        data:{
            table: "Table_"+ getQueryString("tableId").padStart(4,0),
        },
        method:"GET",
        success:function (res) {
            if(res){
                let tmp=JSON.parse(res);
                console.log(tmp);
            }

        }

    })
}*/
function getMenuData() {
    $.ajax({
        url:"../php/menuDataByXSTAR.php?q=getAllData&table=Dishes",
        success:function (res) {
            let menu = JSON.parse(res);
            menuData=menu;
           // getOrderInfo();
            //console.log(menuData);
            for(var i in menu){
                var item=menu[i];
                let judge=type==="water";
                //console.log(item);
                //if( (WATER.indexOf(item.type)!==-1)===judge){
                if( (item.type2 === "Water")===judge){
                    newItem(item);
                }

            }
            typeFilter();
        }
    })
}
function getMenuInfo() {
    $.ajax({
        url:"../php/menuDataByXSTAR.php?q=getAllData&table=MenuInfo",
        success:function (res) {

            let menu = JSON.parse(res);
            menuInfo=menu;
            // console.log(menu);
            for(var i in menu){
                var item=menu[i];

                let judge=type==="water";
                //if( (WATER.indexOf(item.typename)!==-1)===judge){
                if( (item.type2 === "Water")===judge){
                    newContainer(item.typename);
                    newOption(item.typename);
                }

            }
            getMenuData();
        }
    })
}
function findUnitByTypeName(type) {
    for (var i in menuInfo){
        if(menuInfo[i].typename==type){
            if(menuInfo[i].countunit){
                return menuInfo[i].countunit;
            }
            return "份";
        }
    }
}
function parseOrderType(arr) {
    for(value of arr.info){
        if(value.type=="Wein"||value.type=="Kaffee"||value.type=="Getränke"){
            value.type="waterBar";
        }else{
            value.type="kitchen"
        }
    }

}
function sendOrder() {
    if(sedned){
        return;
    }
    sedned = true;
    console.log("sendOrder");
    parseOrderType(Order);

    Order.seat=seat;
    //console.log(Order);
    $.ajax(
        {
            url:"../php/menuDataByXSTAR.php?q=addDishIntoCertainTable",
            data:{
                orderInfo:JSON.stringify(Order),
                children:children,
                timestamp:timestamp
            },
            method:"POST",
            success:function (res) {
                sedned = true;
                if(type==="water" || children==="single" || children=='takeout'){

                    if(res=="good"){
                        window.location.href="index.html"+param;
                    }
                }else{
                    addRound();
                }

                console.log(res);

            },
            complete:function (res) {
                console.log(res);
            }
        }

    )

}

function findItemById(id) {
    for(let i in menuData){
        let tmp=menuData[i];
        if(tmp.dishId==id){
            return tmp;
        }
    }
    return false;
}
function findItemByPId(Pid) {
    for(let i in Order.info){
        let tmp=Order.info[i];
        if(tmp.productId==Pid){
            return tmp;
        }
    }
    return false;
}
function logOrder(id,amount,productId) {
    let item=findItemById(id);
    item.amount=amount;
    item.productId=productId;
    if(Order.info){
        if(Order.info){
            Order.info.push(item);
        }else{

            Order.info.push(item);
        }
    }else{
        Order.info=[];

        Order.info.push(item);

    }
    updateCountAndPrice();
    //console.log(Order);

}

function updateCountAndPrice() {
    let count = 0;
    let price = 0;
    //console.log(Order.info);
    for(let key in Order.info){
        let item = Order.info[key];
     //   console.log(Order.info[key]);

            count+=parseInt( item.amount);

            price+=parseFloat((parseFloat( item.price)*item.amount).toFixed(2));

    }
    Order.count=count;
    Order.price=price;
}
function removeFromArray(pid,array) {
    let i=0;
    let d=false;
    for( i in array){

        if(array[i].productId==pid){
            console.log(array[i]);
            d=true;
            break;
        }
    }
    if(d){
        array.splice(i,1);
    }
    return array;
}
function removeItem(pid) {

     removeFromArray(pid,Order.info);
    updateCountAndPrice();
    console.log(Order);
}

function newOption(id) {
    let li=document.createElement("li");
    li.innerHTML="<a href=\"#"+id+"\" class=\"selected\">"+id+"</a>";
    document.getElementById("sideMenu").appendChild(li);
}
function initial() {
    LoadBasicData();
    /*
    $.ajax(
        {
            url:"../php/getOrder.php",
            data:{
                q:"order",
                shopName:shopName,
                table:tableName
            },
            method:"GET",
            success:function (res) {
                console.log(res);
                if(res){
                    orderInfo =JSON.parse(res);
                    //console.log(orderInfo);
                    showCart(orderInfo);
                    assignInClass("summe",String.Summe+finalPrice);
                }

            }
        }
    );

    */


}


function newItem(item) {
    //console.log(item);

    var row=document.createElement("div");
    item.discribe=item.discribe?item.discribe:String.Current_No_Discribe;
    row.innerHTML="   <div onclick='showDetail(this)' data-dish-id='"+item.dishId+"' class=\"items\">\n" +
        "            <div class=\"itemImg\">\n" +
        "                <img src=\""+item.imagename+"\">\n" +
        "            </div>\n" +
        "            <div class=\"itemDetail\">\n" +
        "                <div class=\"itemDetailTopRow\">\n" +
        "                    <div class=\"itemName\">"+item.name+"</div>\n" +
        "                    <div class=\"itemPrice\"> € "+item.price+"</div>\n" +
        "                </div>\n" +
        "                <div class=\"itemDetailBottomRow\">\n" +
        "                   "+item.discribe+"\n" +
        "                </div>\n" +
        "            </div>\n" +
        "        </div>\n";
  //  console.log(item.type);
    if(document.getElementById(item.type)){
        document.getElementById(item.type).appendChild(row);
    }
    
}
function menuItemMinus() {
    let current =parseInt( document.getElementById("menuAmount").innerText);
    if(current>1){
        current-=1;
    }
    document.getElementById("menuAmount").innerText=current;
    document.getElementById("confirmButton").setAttribute("data-amount",current);
}
function menuItemPlus() {
    let current =parseInt( document.getElementById("menuAmount").innerText);
    current+=1;
    document.getElementById("menuAmount").innerText=current;
    document.getElementById("confirmButton").setAttribute("data-amount",current);
}
function showDetail(target) {
    //console.log(target);
    let name = target.children[1].children[0].children[0].innerHTML;
    let price = target.children[1].children[0].children[1].innerHTML;
    price=price.substr(2);
    let id=target.dataset.dishId;
    let discribe=target.children[1].children[1].innerHTML;
    let imagename=target.children[0].children[0].src;
    // console.log(target.children[1].children[0].children[0].innerHTML);
    document.getElementById("detailName").innerText=name;
    document.getElementById("confirmButton").setAttribute("data-price",parseFloat(price));
    document.getElementById("confirmButton").setAttribute("data-name",name);
    document.getElementById("confirmButton").setAttribute("data-dish-id",id);
  //  console.log(price);
    document.getElementById("menuAmount").innerText=0;
    document.getElementById("detailPrice").innerText=parseFloat(price)+" € ";
    let item=findItemById(id);

    assignInClass("itemUnit","/ "+ findUnitByTypeName(item.type));
    document.getElementById("detailDescribe").innerText=discribe;
    $("#imagename").attr("src",imagename);
    document.getElementById("detailPage").style.transform="translateX(0)";
    document.getElementById("confirmButton").setAttribute("data-amount",1);
}
function hideDetail() {
    document.getElementById("detailPage").style.transform="translateX(100%)";

}

function newContainer(item) {


    var row=document.createElement("div");
    row.innerHTML="  <div class=\"menuItemContainer\" id=\""+item+"\" >\n" +
        "        <div class=\"itemTitle\" >\n" +
        "           "+item+"\n" +
        "        </div>\n" +
        "    </div>";
    //   console.log(item.type);

    document.getElementById("totalContainer").appendChild(row);
}


function getRound() {
    if(children!='single' && children!='takeout' && type!='water'){
        $.ajax({
            url:"../php/menuDataByXSTAR.php?q=getCurrentRound",
            data:{
                tablenr:tableId,
                seat:seat
            },
            method:"GET",
            success:function (res) {
                console.log(res);
                CurrentRound=res;
                if(CurrentRound>=MAXROUND){
                   // disableButton("Order");
                    timeOut=true;
                    window.history.go(-1);
                    //alert(String.timeOut)//jxy
                }

            }
        })
    }
}

function getFinalTime() {
    if(children!='single' && children!='takeout' && type!='water'){
        $.ajax({
            url:"../php/menuDataByXSTAR.php?q=getBuffetTime",
            data:{
                tablenr:tableId,
                seat:seat
            },
            method:"GET",
            success:function (res) {
                res=res.replace(/\-/g, "/");//jxy
                //console.log(res);//jxy
                //let  NextTime=new Date(res).getTime()+ONEMINUTE*MAXTIME+ONEMINUTE*60*2; //jxy
                let  FinalTime=new Date(res).getTime()+ONEMINUTE*MAXTIME;//jxy
                console.log("结束时间:"+new Date(FinalTime)+"***"+new Date());//jxy

                //if(NextTime<new Date().getTime()){//jxy
                if(FinalTime<new Date().getTime()){//jxy

                    timeOut=true;
                    alert(String.timeOut);
                    window.history.go(-1);
                }
            }
        })
    }
}
function getNextTime() {
    if(children!='single' && children!='takeout' && type!='water'){
        $.ajax({
            url:"../php/menuDataByXSTAR.php?q=getLastOrderInTable",
            data:{
                tablenr:tableId,
                seat:seat
            },
            method:"GET",
            success:function (res) {

                //res=res.replace(/\-/g, "/").slice(0,-7);
                res=res.replace(/\-/g, "/");//jxy
                //console.log(res);
                //NextTime=new Date(res).getTime()+ONEMINUTE*WAITTIME+ONEMINUTE*60*2;//jxy
                NextTime=new Date(res).getTime()+ONEMINUTE*WAITTIME;
                //console.log("下轮时间:"+ NextTime+"***"+new Date().getTime());
                console.log("下轮时间:"+ new Date(NextTime)+"***"+new Date());
                if(NextTime>new Date().getTime()){
                    //initialCountDown();
                    window.history.go(-1);
                }
            }
        })
    }
}