//configue and initial;
let Order={};
let finalePrice=0;
let count=0;
let first=true;
let sended = false;
const ROOTURL="../php/menuDataByXSTAR.php";
$( document ).ready(function () {
    initial();

}); 
function initial() {
    LoadBasicData();
    getMenuInfo();

    first=true;

}
function sendOrder(item) {
    if(sended){
        return;
    }
    sended = true;
    //console.log(tableName);
    $.ajax({
        type:"POST",
        url:"../php/menuDataByXSTAR.php?q=addOrder",
        data:{
            tablenr:tableId,
            paymentId:item,
            tableName:tableName,
        },

        success:function (res) {
            console.log(res);
            if(children === "takeout"){
                setTimeout(gotoThanks(),2000);
                return;
            }
            if(res=="good"){
              setTimeout(gotoHome(),2000);
            }else{
                alert(res);
            }
        }
    })
}
function gotoHome() {
    window.location.href="thanks.html"+param;//"index_b.html?tableName="+tableName+"&tableId="+tableId+"&shopName="+shopName;
}
function gotoThanks() {
    window.location.href="thanks2.html"+param;//"index_b.html?tableName="+tableName+"&tableId="+tableId+"&shopName="+shopName;
}
function showPaymentMethod() {
        $('.as-container').remove();
        let   as = new ActionSheet({
            buttons: {
                "Bar": function (e) {
                    sendOrder("Bar");
                    as.hide();
                },
                "EC Karte": function (e) {
                    sendOrder("EC Karte");
                    as.hide();
                },
                /*"QR code": function (e) {
                    sendOrder("QR code");
                    as.hide();
                },*/

            }
        }).show() ;


   //
}
function getMenuInfo() {
    $.ajax({
        url:"../php/menuDataByXSTAR.php?q=getMenuInfo",
        success:function (res) {
            let menu = JSON.parse(res);

            // console.log(menu);
            for(var i in menu){
                var item=menu[i];
                newContainer(item.typename);
               // newOption(item.typename);
            }
            getOrderInfo();

        }
    })
}
function getMenuData() {
    $.ajax({
        url:"../php/menuDataByXSTAR.php?q=getAllData&table=Dishes",
        success:function (res) {
            menuData=JSON.parse(res);
           // console.log(menuData);
            Order=filterFreeDishes(Order);
            Order=mergeOrders(Order);
            for(var i in menuData){
                var item=menuData[i];

                for(let t in Order){
                    if(item.dishId==Order[t].dishId){
                      //  console.log(true);
                      var amountNow=  document.getElementById(item.type).children[0].children[0].innerHTML;
                      amountNow=parseInt(amountNow);
                      amountNow+=1;
                        document.getElementById(item.type).children[0].children[0].innerHTML=amountNow;
                        document.getElementById(item.type).style.display="";
                        item.price = Order[t].price;
                        newItem(item,Order[t].amount);
                    }
                  //  console.log(true);
                }

            }
            assignInClass("totalPrice",finalePrice.toFixed(2));
            assignInClass("totalAmount",count);
        }
    })
}
function findItemByDishId(arr,item) {
    for(let i in arr){
        if(item.dishId==arr[i].dishId){
            return i;
        }
    }
    return -1;
}
function mergeOrders(Orders) {
    let tmp=[];
    for(let item of Orders){
        let n=findItemByDishId(tmp,item);
        if(n!=-1){
             tmp[n].amount=parseInt(item.amount)+parseInt(tmp[n].amount);
        }else{
            tmp.push(item);
        }
    }
  //  console.log(tmp);

    return tmp;


}
function getOrderInfo() {
    $.ajax({
        url:"../php/menuDataByXSTAR.php?q=getAllData",
        data:{
            table: "Table_"+ getQueryString("tableId").padStart(4,0),
        },
        method:"GET",
        success:function (res) {

            Order=JSON.parse(res);
          //  console.log(Order);
            getMenuData();

        }

    })
}

function newContainer(item) {


    var row=document.createElement("div");
    row.setAttribute("class","menuItemContainer");
    row.setAttribute("id",item);
    row.setAttribute("style","display:none");
    row.innerHTML= "  <div class=\"itemTitle\">\n" +
        "            "+item+" : <span class=\"typeCount\">0</span> dishes\n" +
        "        </div>"

    //   console.log(item.type);

    document.getElementById("totalContainer").appendChild(row);
}
function newItem(item,amount) {
    // console.log(item);
    onePrice = parseFloat(item.price);
    //console.log(item.type);
    
    finalePrice+=onePrice*parseFloat(amount);
    count+=1;
    var row=document.createElement("div");

    row.setAttribute("data-dish-id",item.dishId);
    row.setAttribute("class","orderContainer");
    item.discibe=item.discibe?item.discibe:"暂时没有描述";
    row.innerHTML="    <div class=\"amountInfo\">"+parseInt(amount)+"</div>\n" +
        "            <div class=\"dishInfo\">\n" +
        "                <div class=\"dishName\">"+item.name+"</div>\n" +
        "                <div  class=\"dishSinglePrice\"><span class=\"itemPrice\">"+onePrice.toFixed(2)+"</span>€/份</div>\n" +
        "            </div>\n" +
        "            <div class=\"price\">"+(onePrice*parseFloat(amount)).toFixed(2)+"€</div>";


    //  console.log(item.type);

    document.getElementById(item.type).appendChild(row);
}
function filterFreeDishes(Order) {
    let dishes=[];
    for(item of Order){
        let tmp=findItemById(item.dishId);
        //console.log(tmp);
        if(tmp.type === "Buffet"  || tmp.type2 === "Water"  || item.children==="single"  || item.children==="takeout"){
            //除去price=0的Buffet
            if(!((item.children==="single" || item.children==="takeout") && tmp.type === "Buffet")){
                dishes.push(item);
            }
        }
    }
    return dishes;
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