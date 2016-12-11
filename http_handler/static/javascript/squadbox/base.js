
$('.subscribe-submit').click(function() {
	var email = $('.subscribe-input').val();
	var params = {
		'group_name' : 'squadbox-discuss',
		'email': email
		};
	$.post('/subscribe_group', params, function(res){
		if (res.status) {
			$('#subscribe-success').show();
		} else {
			$('#subscribe-failure').show();
		}
	});
});
