
$('.subscribe-submit').click(function() {
	
	var params = {
		'group_name' : 'squadbox-discuss',
		'email': email
		};
	$.post('/subscribe_group', params, function(res){
		if (res.status) {
			
		}
	});
});
