$(document).ready(function() {

	$('form').on('submit', function(event) {

		$.ajax({
			data : {
				name : $('#name').val(),
				persons : $('#persons').val(),
        section : $('#section').val()

			},
			type : 'POST',
			url : '/js/tables/add'
		})
		.done(function(data) {

			if (data.error) {
				$('#error').text(data.error).show();
				$('#success').hide();
			}
			else {
				$('#success').text(data.success).show();
				$('#error').hide();
			}

		});

		event.preventDefault();

	});

});
