
$('.subscribe-submit').click(function() {
	var email = $('.subscribe-input').val();
	window.location = 'http://murmur.csail.mit.edu/subscribe_get?group_name=squadbox-discuss&email=' + email;
});
