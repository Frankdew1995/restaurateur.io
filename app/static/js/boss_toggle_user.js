

$(function() {
    $('.onoffswitch-checkbox').change(function() {

      const userId = $(this).attr('id');
      const status = $(this).prop('checked');

      const info = {'userId':userId,
                      'inUse': status}

      console.log(info);


      data = JSON.stringify(info);

      var request = new XMLHttpRequest();
      request.open('POST', '/user/switch', true);
      request.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
      request.send(data);




    })
  })
