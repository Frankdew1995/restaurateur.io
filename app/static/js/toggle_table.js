

$(function() {
    $('.onoffswitch-checkbox').change(function() {

      const tableId = $(this).attr('id');
      const status = $(this).prop('checked');

      const info = {'tableName':tableId,
                      'isOn': status}

      console.log(info);


      data = JSON.stringify(info);

      var request = new XMLHttpRequest();
      request.open('POST', '/table/switch', true);
      request.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
      request.send(data);




    })
  })
