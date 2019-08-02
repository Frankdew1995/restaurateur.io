
$( document ).ready(function () {
    initial();

});
function initial() {
    lan=getQueryString("Lan")?getQueryString("Lan"):DEFAULTLANGUAGE;
    multiLanguage(lan);
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