//configue and initial;


let Order = {};
let waiting=false;
let CurrentRound=0;
let NextTime=new Date();
let FinalTime=new Date();//jxy
let timeOut=false;

$( document ).ready(function () { 
    initial();

});

function initial() {
    LoadBasicData();
    //getNextTime();
    //getRound();
    //getFinalTime();
    getMenuData();
    $("#ConfirmPagep1").attr("placeholder",String.ConfirmPagep1);
    $(".zy_header").html(String.IndexPage1);
    $(".img1").attr("src","../img/"+String.Button1);
    $(".img2").attr("src","../img/"+String.Button2);
    $(".img3").attr("src","../img/"+String.Button3);
    $(".img4").attr("src","../img/"+String.Button4);
}


 
function initialCountDown() {
    // Set the date we're counting down to

    document.getElementById("nextRound").style.display="";
    let countDownDate = NextTime;
    waiting=true;
    let x = setInterval(function () {
        let now = new Date().getTime();
        let distance = countDownDate - now;
        //console.log(distance);
        let minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        let seconds = Math.floor((distance % (1000 * 60)) / 1000);
        setCountDown(pad(minutes,2) + ":" + pad(seconds,2));
        if (distance < 0 || CurrentRound == 0 || CurrentRound >= MAXROUND) {//jxy  第0轮不用等 大于MAXROUND轮不用等
            document.getElementById("nextRound").style.display="none";
            clearInterval(x);
            waiting=false;

        }
    }, 1000);


}
function check() {
    if(IsBusinessHours()){
        if(!waiting&&!timeOut){
        navigateTo('menu.html'+param+'&type=normal')
        }else if(waiting){
            alert(String.countDownOver);
        }else if(timeOut){
            alert(String.timeOut)
        }
    }else{
        alert(String.BusinessHoursMsg);
    }
}
function drink() {
    if(IsBusinessHours()){
        navigateTo('menu.html'+param+'&type=water');
    }else{
        alert(String.BusinessHoursMsg);
    }
}

function getOrderInfo() {
    $.ajax({
        url:"../php/menuDataByXSTAR.php?q=getAllData",
        data:{
            table: "Table_"+ PrefixInteger( getQueryString("tableId"),4),
        },
        method:"GET",
        success:function (res) {
            //console.log(res);
            Order=JSON.parse(res);

            for(i in Order){
                if(Order[i]['seat'] == seat && Order[i]['children'] != children){
                    children = Order[i]['children'];
                    window.location.href="index.html"+getParam();//jxy
                }
            }
            //console.log(Order[0]['children']);

            if(res){
                if(Order){
                    showSnackBar(String.Sended);
                }
                //console.log(Order);
                Order=filterFreeDishes(Order);
                //console.log(Order);
                if(Order.length===0){
                    document.getElementById("orderCount").style.display="none";
                }else{

                    document.getElementById("orderCount").style.display="";

                }

                document.getElementById("orderCount").innerText=Order.length;


            }

        }

    })
}
function getFinalTime() {
    if(children!='single' && children!='takeout'){
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
                }
            }
        })
    }
}
function getNextTime() {
    if(children!='single' && children!='takeout'){
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
                    initialCountDown();
                }
            }
        })
    }
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
function getRound() {
    if(children!='single' && children!='takeout'){
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
                    //alert(String.timeOut)//jxy
                }

            }
        })
    }
}
var called = false;
function Callservice() {
    if(IsBusinessHours){
        //
        if(!called){
            called = true;
            $.ajax({
                url:"../php/menuDataByXSTAR.php?q=callService",
                data:{
                    tableName:tableName,
                    seat:seat
                },
                method:"POST",
                success:function (res) {
                    showSnackBar(String.Ok)
                    called = false;
                }
            });
        }

    }else{
        showSnackBar(String.BusinessHoursMsg)
    }
}

function setCountDown(Time) {

    assignInClass("NextRound","("+CurrentRound+")"+Time);

}
function showSnackBar(text) {
    let x = document.getElementById("snackbar");
    x.innerHTML=text;
    x.className = "show";
    setTimeout(function(){ x.className = x.className.replace("show", ""); }, 3000);
}

function PrefixInteger(num, length) {
    return (Array(length).join('0') + num).slice(-length);
}
function pad(num, size) {
    var s = num+"";
    while (s.length < size) s = "0" + s;
    return s;
}

function disableButton(id) {
    document.getElementById(id).disabled=true;
}
function enableOrder(id) {
    document.getElementById(id).disabled=false;

}
function pay() {
    let ok=confirm(String.confirmFinish);
    if(ok){
        navigateTo('payment.html'+param);
    }

}

