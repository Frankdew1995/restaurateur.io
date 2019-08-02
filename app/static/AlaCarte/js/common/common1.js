const ONEMINUTE=60000;

const MAXDISH=5;
const WATER=['Getränke', 'Wein', 'Eis & Kaffee','Buffet'];
const WAITTIME=10;
const MAXROUND=10;
const MAXTIME=150;
const CHILDRENPRICE=0.5;//jxy 儿童餐比例
const DEFAULTLANGUAGE="CN";
//const BUFFETID="DE2018050800010043";//jxy 
const BUFFETID="DE201805080001000";//自助餐的dishid

let lan=DEFAULTLANGUAGE;
let param="";
let tableName= getQueryString("tableName");
let shopName= getQueryString("shopName");
let tableId=getQueryString("tableId");
let seat=getQueryString("seat");
let children=getQueryString("children");//jxy
let String={};
function confirmBuffet() {
    
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
        let tmp=findItemById(item.dishId);
        if(WATER.indexOf(tmp.type)!=-1){
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
    assignInClass("seat",""+(parseInt( seat)+1));

}

