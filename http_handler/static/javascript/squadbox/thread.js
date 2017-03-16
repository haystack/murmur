$(document).ready(function(){

	var approve_button = $('#btn-approve'),
		reject_button = $('#btn-reject'),
		blacklist_box = $('#blacklist-check'),
		whitelist_check = $('#whitelist-check')[0],
		blacklist_check = $('#blacklist-check')[0],
		user_email = $.trim($('#user_email').text()),
		sender_email = $.trim($('#sender-email').text()),
		group_name = $.trim($('#group-name').text()),
		post_id = $.trim($('#post-id').text());

	approve_button.click(function(){

		var params1 = {
			'group_name' : group_name,
			'post_id' : post_id, 
		}

		var params2 = {
			'group_name' : group_name,
			'sender' : sender_email,
		}

		var add_to_whitelist = (whitelist_check.checked);
		var add_to_blacklist = (blacklist_check.checked);

		if (add_to_blacklist) {
			alert("Error: you've selected to approve this email, but blacklist the sender.");
			return;
		}

		$.post('/approve_post', params1,
			function(res) { 
				console.log("add to whitelist: " + add_to_whitelist);
				if (add_to_whitelist) {
					notify(res, false);
					if (res.status) {
						console.log("post to whitelist");
						$.post('/whitelist', params2, 
							function(res){
								notify(res, true);
							}
						);
					}
				} else {
					notify(res, true);
					console.log(res);
				}
				setTimeout(function(){
					window.location = '/dashboard';
				},1000);
			}
		);
	});

	reject_button.click(function(){

		var params1 = {
			'group_name' : group_name,
			'post_id' : post_id, 
		}

		var params2 = {
			'group_name' : group_name,
			'sender' : sender_email,
		}

		var add_to_whitelist = (whitelist_check.checked);
		var add_to_blacklist = (blacklist_check.checked);

		if (add_to_whitelist) {
			alert("Error: you've selected to reject this email, but whitelist the sender.");
			return;
		}

		$.post('/reject_post', params1,
			function(res) { 
				if (add_to_blacklist) {
					notify(res, false);
					if (res.status) {
						$.post('/blacklist', params2, 
							function(res){
								notify(res, true);
							}
						);
					}
				} else {
					notify(res, true);
					console.log(res);
				}
				setTimeout(function(){
					window.location = '/dashboard';
				},1000);
			}
		);
	});

	function deselect_other(which) {
		if (which == 'white') blacklist_check.checked = false;
		else if (which == 'black') whitelist_check.checked = false;
	}

	$('#blacklist-check').click(function(){
		deselect_other('black');
	});

	$('#whitelist-check').click(function(){
		deselect_other('white');
	});

});