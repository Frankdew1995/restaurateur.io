const ONEMINUTE=60000;

const MAXDISH=5;
const WATER=['Getränke', 'Wein', 'Eis & Kaffee','Buffet'];
const WAITTIME=10;
const MAXROUND=10;
const MAXTIME=150;
const CHILDRENPRICE=0.5;//jxy 儿童餐比例
const DEFAULTLANGUAGE="DE";
//const BUFFETID="DE2018050800010043";//jxy 
const BUFFETID="Buffet";//自助餐的dishid
const DateCountUrl = "../../time/getDateCount.php";
const AREA = new Array('A', 'B', 'C','D','E', 'F', 'G','H','I', 'J', 'K','L','M', 'N', 'O','P','Q', 'R', 'S','T','U', 'V', 'W','X', 'Y','Z');

const timeLength = 0.5; //打印间隔 单位s
const getDataTimeLength = 2;//获取数据间隔 单位s 

const BusinessHoursStart = "00:00:01";//营业时间开始
const BusinessHoursEnd = "23:59:00";//营业时间结束

let lan=DEFAULTLANGUAGE;
let param="";
let tableName= getQueryString("tableName");
let shopName= getQueryString("shopName");
let tableId=getQueryString("tableId");
let seat=getQueryString("seat");
let children=getQueryString("children");//jxy
let String={};
function confirmBuffet() {
    $.ajax({
        url:"../php/menuDataByXSTAR.php?q=getAllDishesInTable",//从桌子表，获取点餐
        data:{
            tablenr:tableId,
            usingSended:0
        },
        method:"GET",
        success:function (res) {
            //console.log(res);
            let order=JSON.parse(res);
            for(item of order){
                if(item.type != "Buffet"){
                    if(item.seat==seat){
                        return;
                    }
                }
            }
            if(window.location.href.indexOf("Confirm")===-1){
                if(children == "takeout"){
                    window.location.href="Confirm1.html"+param
                }else{
                    window.location.href="Confirm.html"+param
                }
            }


        }
    })
}
function IsBusinessHours(){
    var now = new Date();
    var year = now.getFullYear();
    var month = now.getMonth();
    var date = now.getDate();
    var hour = now.getHours();
    var minutes = now.getMinutes();
    var second = now.getSeconds(); 
    month=month+1; 
    month<10?month='0'+month:month; 
    hour<10?hour='0'+hour:hour; 
    minutes<10?minutes='0'+minutes:minutes; 

    var s_time = year + '/' + month + '/' + date + ' ' + BusinessHoursStart; 
    var e_time = year + '/' + month + '/' + date + ' ' + BusinessHoursEnd; 

    var st = new Date(Date.parse(s_time));  
    var et = new Date(Date.parse(e_time));  

    if(!st){ 
        var arr = s_time.split(/[- : \/]/);
        st = new Date(arr[0], arr[1]-1, arr[2], arr[3], arr[4], arr[5]);
        arr = e_time.split(/[- : \/]/);
        et = new Date(arr[0], arr[1]-1, arr[2], arr[3], arr[4], arr[5]);
    }

    if(now>= st && now <=et){  
        return true;
    }else{
        return false;
    }  

}
function getParam() {//jxy
    var p ='?tableName='+tableName+'&shopName='+shopName+'&tableId='+tableId+'&Lan='+lan+'&seat='+seat+'&children='+children;//jxy
    return p;
}

function LoadBasicData() {

    tableName= getQueryString("tableName");
    shopName= getQueryString("shopName");
    tableId=getQueryString("tableId");
    seat=getQueryString("seat");
    lan=getQueryString("Lan")?getQueryString("Lan"):DEFAULTLANGUAGE;
    children=getQueryString("children");//jxy
    multiLanguage(lan);
    param='?tableName='+tableName+'&shopName='+shopName+'&tableId='+tableId+'&Lan='+lan+'&seat='+seat+'&children='+children;//jxy
    showTableAndShopName();
    confirmBuffet();

}
function filterFreeDishes(Order) {
    let dishes=[];
    for(item of Order){
        //let tmp=findItemById(item.dishId);
        if(item.price > 0){
            dishes.push(item);
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


function multiLanguage(config) {
    switch (config){
        case "CN":String=stringsCN;break;
        case "EN":String=stringsEN;break;
        case "DE":String=stringsDE;break;
    }
    for(let key of Object.keys(String)){
        assignInClass("lan_"+key,String[key]);
    }
}
function assignInClass(className,text) { //给对象设值
    var tmp=document.getElementsByClassName(className);
   // console.log(tmp);
    if(tmp.length>0){
        for(i in tmp){
            tmp[i].innerHTML=text;
        }
    }
}



function navigateTo(url) {
    window.location.href=url;
}
function getQueryString(name) {
    var reg = new RegExp("(^|&)" + name + "=([^&]*)(&|$)", "i");
    var r = window.location.search.substr(1).match(reg);
    if (r != null) return unescape(r[2]); return null;
}
function toggleDisplay(item) {
    let str=item.style.display;
    console.log(str);
    if(str=="none"){
        item.style.display="block";
    }else{
        item.style.display="none";
    }
}
function getMenuData() {

    $.ajax({
        url:"../php/menuDataByXSTAR.php?q=getAllData&table=Dishes",
        success:function (res) {

            menuData=JSON.parse(res);

        }
    })

}
function showTableAndShopName() {

    tableName= getQueryString("tableName");
    shopName= getQueryString("shopName");

    assignInClass("shopName",""+shopName);
    assignInClass("tableName",String.Tisch+tableName);
    assignInClass("seat",""+(parseInt( seat)));

}

