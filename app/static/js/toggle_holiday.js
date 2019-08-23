

$(function() {
    $('.onoffswitch-checkbox').change(function() {

      const holidayId = $(this).attr('id');
      const status = $(this).prop('checked');

      const info = {'holiday_id':holidayId,
                      'inUse': status}

      console.log(info);

      data = JSON.stringify(info);

      var request = new XMLHttpRequest();
      request.open('POST', '/holiday/switch', true);
      request.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
      request.send(data);

    })
  })
