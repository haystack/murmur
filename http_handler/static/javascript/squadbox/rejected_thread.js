$(document).ready(function() {
	var message_link = $('#message-link'),
		send_btn = $('#send-btn');
		cancel_btn = $('#cancel-btn'),
		notify_link = $('#notify-link')[0],
		message_form = $('#message-form')[0],
		admin_msg = $('#admin-message')[0],
		show_msg = $('#show-msg'),
		post_text = $('#post-text')[0];

	message_link.click(function() {
		message_form.style.display = 'inline';
		notify_link.style.display = 'none';
	});

	cancel_btn.click(function() {
		message_form.style.display = 'none';
		notify_link.style.display = 'inline';
	});


	show_msg.click(function() {
		if (post_text.style.display == 'none') {
			post_text.style.display = 'inline';
			$('#show-msg')[0].innerHTML = 'Hide message text';
		} else {
			post_text.style.display = 'none';
			$('#show-msg')[0].innerHTML = 'Show message text'
		}
	});

	// send_btn.click(function() {
	// 	var params = {}
	// });
});