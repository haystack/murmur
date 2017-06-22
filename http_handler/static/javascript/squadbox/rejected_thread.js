$(document).ready(function() {
	var message_link = $('#message-link'),
		send_btn = $('#send-btn');
		cancel_btn = $('#cancel-btn'),
		delete_btn = $('#delete-btn'),
		notify_link = $('#notify-link')[0],
		message_form = $('#message-form')[0],
		admin_msg = $('#admin-message')[0],
		show_msg = $('#show-msg'),
		post_text = $('#post-text')[0],
		post_id = $('#post-id')[0].innerHTML,
		thread_id = $('#thread-id')[0].innerHTML,
		group_name = $('#group-name')[0].innerHTML;

	message_link.click(function() {
		message_form.style.display = 'inline';
		notify_link.style.display = 'none';
		delete_btn[0].style.display = 'none';
	});

	cancel_btn.click(function() {
		message_form.style.display = 'none';
		notify_link.style.display = 'inline';
		delete_btn[0].style.display = 'inline';
	});

	delete_btn.click(function() {
		if (confirm("Are you sure you want to delete this message? This cannot be undone.")) {
			$.post('delete_post', {'id' : post_id, 'thread_id' : thread_id}, 
				function(res) {
					if (res.status) window.location.href = "/groups/" + group_name + "/rejected";
					notify(res, true);
				}
			);
		} 
	});

	show_msg.click(function() {
		if (post_text.style.display == 'none') {
			post_text.style.display = 'inline';
			$('#show-msg')[0].innerHTML = 'Hide message text';
		} else {
			post_text.style.display = 'none';
			$('#show-msg')[0].innerHTML = 'Show message text';
		}
	});

	// send_btn.click(function() {
	// 	var params = {}
	// });
});