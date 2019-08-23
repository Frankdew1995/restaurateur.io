

$(function() {
    $('.onoffswitch-checkbox').change(function() {

      const dishId = $(this).attr('id');
      const status = $(this).prop('checked');

      const info = {'dish_id':dishId,
                      'inUse': status}

      console.log(info);

      data = JSON.stringify(info);

      var request = new XMLHttpRequest();
      request.open('POST', '/dish/switch', true);
      request.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
      request.send(data);

    })
  })
