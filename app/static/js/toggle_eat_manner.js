

$(function() {
    $('.onoffswitch-checkbox').change(function() {

      const dishId = $(this).attr('id');

      const mannerName = $(this).attr('name');

      const status = $(this).prop('checked');

      const info = {}

      // available as takeaway
      if (mannerName.trim() === "takeaway"){

        info.is_takeaway = status;
        info.dishId = dishId;

      } else if (mannerName.trim() === "alacarte") {

        info.is_a_la_carte = status;
        info.dishId = dishId;

      }

      // console.log(info);


      data = JSON.stringify(info);

      console.log(data);

      // var request = new XMLHttpRequest();
      // request.open('POST', '/eat/manner/switch', true);
      // request.setRequestHeader('Content-Type', 'application/json; charset=UTF-8');
      // request.send(data);

    })
  })
