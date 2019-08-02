let dateCount = 0;
$( document ).ready(function () {
    initial();

});
function initial() {
    LoadBasicData();
    //getCurrentPrice();//jxy
    setInterval(function() {
        $('.timeNow').text(getdate());
    }, 1000);
    //startBuffet('single');
    $(".ConfirmPage1").html(String.ConfirmPage1);
    $("#ConfirmPagep1").attr("placeholder",String.ConfirmPagep1);
    $("#ConfirmPage2").html(String.ConfirmPage2);
    $("#ConfirmPage3").html(String.ConfirmPage3);
    $("#ConfirmPage4").html(String.ConfirmPage4);
    $("#ConfirmPage5").html(tableName);
    $("#ConfirmPage6").html(String.ConfirmPage6);
    $(".ConfirmPage7").html(String.ConfirmPage7);
    $("#ConfirmPage8").html(String.ConfirmPage8);
    $("#ConfirmPage9").html(String.ConfirmPage9);
    $("#ConfirmPage10").html(String.ConfirmPage10);
    $("#ConfirmPage11").html(String.ConfirmPage11);
    $("#ConfirmPage12").html(String.ConfirmPage12);
}
function getdate(){
    var today = new Date();
    var h = today.getHours();
    var m = today.getMinutes();
    var s = today.getSeconds();
    if(s<10){
        s = "0"+s;
    }
    return (h+":"+m+":"+s);
}


function getCurrentPrice(){ //JXY
    var myDate = new Date();//获取系统当前时间
    var nowdate = myDate.getFullYear() + "-" + (parseInt(myDate.getMonth())+1) + "-" + myDate.getDate();
    console.log(nowdate);
    $.ajax(
        {
            url:DateCountUrl,
            data:{
                nowdate:nowdate
            },
            method:"GET",
            success:function (res) {
                //console.log(res);
                dateCount = res;

                var p = "price";
                if(dateCount >0){
                    p = "price567";
                }
                var hours = new Date().getHours() ;  
                if(hours > 16){
                    p = p + "_pm";
                }

                $.ajax({
                    url:"../php/menuDataByXSTAR.php?q=getCurrentPrice",
                    data:{
                        p:p
                    },
                    method:"GET",
                    success:function (res) {
                        console.log(res);
                        document.getElementById('CurrentPrice').innerHTML = res;
                    }
                })

            },
            complete:function (res) {
                //console.log(res);
            }
        }

    )
    
}

function startBuffet(c) {
    if(IsBusinessHours()){
        $.ajax({
            url:"../php/menuDataByXSTAR.php?q=addBuffetInTable",
            data:{
                tablenr:tableId,
                seat:seat,
                children:c,//jxy
                dateCount:dateCount
            },
            method:"POST",
            success:function (res) {
                console.log(res);
                if(res == 'no' || res == 'yes' || res == 'single'|| res == 'takeout'){
                    children = res;
                }
                if(res == 'good'){
                    children = c;
                }
                window.location.href="index.html"+getParam();//jxy
            }
        })
    }else{
        alert(String.BusinessHoursMsg);
    }
    
}
