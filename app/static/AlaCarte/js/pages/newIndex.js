//configue and initial;

let Order = {};
let waiting=true;
let lan="DE";
$( document ).ready(function () {
    initial();

});
function initial() {
    lan=getQueryString("Lan")?getQueryString("Lan"):"DE";
    multiLanguage(getQueryString("Lan")?getQueryString("Lan"):"DE");
    showTableAndShopName();

    getMenuData();

}

function initialCountDown() {
    // Set the date we're counting down to
    disableButton("Order");
    let now = new Date();
    now.setMinutes(10);
    //  console.log(now);
    let countDownDate = new Date().getTime() +30000;// 600000;
    //   console.log(countDownDate);
// Update the count down every 1 second
    let x = setInterval(function () {
        let now = new Date().getTime();
        let distance = countDownDate - now;
        let minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        let seconds = Math.floor((distance % (1000 * 60)) / 1000);
        setCountDown(pad(minutes,2) + ":" + pad(seconds,2));
        if (distance < 0) {
            clearInterval(x);
            waiting=false;
            enableOrder("Order");

        }
    }, 1000);


}
function disableButton(id) {
    document.getElementById(id).disabled="true";
}
function enableOrder(id) {
    document.getElementById(id).disabled="false";

}
function pad(num, size) {
    var s = num+"";
    while (s.length < size) s = "0" + s;
    return s;
}
function setCountDown(Time) {

    assignInClass("NextRound","D:"+Time);

}
function getMenuData() {

    $.ajax({
        url:"../php/menuDataByXSTAR.php?q=getAllData&table=Dishes",
        success:function (res) {

            menuData=JSON.parse(res);

            getOrderInfo();
        }
    })

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
            console.log(Order);
            if(res){
                console.log(Order.length);
                if(Order.length==0){
                    document.getElementById("orderCount").style.display="none";
                }else{
                    initialCountDown();
                    document.getElementById("orderCount").style.display="";
                    let x = document.getElementById("snackbar");
                    // Add the "show" class to DIV
                    x.className = "show";
                    // After 3 seconds, remove the show class from DIV
                    setTimeout(function(){ x.className = x.className.replace("show", ""); }, 3000);
                }
                document.getElementById("orderCount").innerText=Order.length;


            }

        }

    })
}
