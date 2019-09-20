
function completeOrder(){

  const completeBtn= document.getElementsByClassName('btn btn-success complete');

  // convert HTMLCollection to Array Object so that forEach can be used.
  var convertedBtn = Array.prototype.slice.call(completeBtn);

  convertedBtn.forEach(function(btn){

    btn.addEventListener("click", function(){

      const orderId = btn.getAttribute('id');

      alert(`确定结束订单${orderId}吗?`);

      const idInfo = {'id': orderId};

      const data = JSON.stringify(idInfo);

      console.log(data);

    

      // var request = new XMLHttpRequest();
      // request.open('POST', '/order/pickup', true);
      // request.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8');
      // request.send(data);

    });



  }

)


};

completeOrder();
