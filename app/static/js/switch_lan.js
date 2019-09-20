
const deBtn = document.getElementById('setDE');

const enBtn = document.getElementById('setEN');

const zhBtn = document.getElementById('setZH');

const nlBtn = document.getElementById('setNL');

const lanBtns = [deBtn, enBtn, zhBtn, nlBtn];


lanBtns.forEach(function(item){

  item.addEventListener("click", function(event){

    const targetLan = item.textContent.trim();

    const info = {};

    info.lan = targetLan;

    const data = JSON.stringify(info);


    var request = new XMLHttpRequest();
    request.open('POST', '/language/settings', true);
    // Send the order data to the server via Post method
    request.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
    request.send(data);

    console.log(data);

  })

});
