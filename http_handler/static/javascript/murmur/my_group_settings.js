$(document).ready(function(){
	
	let user_name = $.trim($('#user_email').text());
	 	group_name = $.trim($("#group-name").text());
		btn_add_dissimulate = $("#btn-add-dissimulate"),
		btn_delete_dissimulate = $("#btn-delete-dissimulate");
		btn_save_settings = $("#btn-save-settings");
		btn_cancel_settings = $("#btn-cancel-settings");
		selectRows = $(".my_row");
		modeInput = $('input[name="tag-mode"]');
		selectTags = $('img[data-type="tag-select"]'); // select elements (block/check icons)
		tags = $(".tag").toArray().map(e => e.innerHTML);
		selectTagsSet = new Set(selectTags.toArray());
		followedTags = new Set(tag_subscription["followed"]);
		mutedTags = new Set(tag_subscription["muted"]);
		swapping = false;
	
	getSavedTagSubscription();

	// Gray out notifications and tag subscription section to indicate no emails will be sent
	if ($('#no-emails').is(":checked")) {
		$('#notifications-area').addClass("gray");
		$('#tag-subscription-area').addClass("gray");
		$('img[data-type="tag-select"]').classList.add("inactive");
	}
	
	// Remove gray from notifications and tag subscription section if email delivery changes
	$('input[type=radio][name=email-delivery]').change(function() {
		let notifications = $('#notifications-area');
			tagSubscription = $('#tag-subscription-area');
		if ($('#no-emails').is(":checked")) {
			notifications.addClass("gray");
			tagSubscription.addClass("gray");
			$('input[type=checkbox][name=notifications]').removeAttr("checked");
		} else {
			notifications.removeClass("gray");
			tagSubscription.removeClass("gray");
		}
	});

	let donotsend_members_table = $('#donotsend-members-table').DataTable({
		"columns": [ { 'orderable': false}, null],
		"order": [[1, "asc"]],
		responsive: true
	});

	let tag_subscription_table = $("#tag-subscription-table").DataTable({
		"columns": [ { 'orderable': false}, null, null, null],
		"order": [[1, "asc"]],
		responsive: {
			details: {
				type: 'column',
				target: 'tr'
			}
		},
	});

	let tag_demo_table = $("#tag-demo-table").DataTable({
		"columns": [ { 'orderable': false}, null, null, null],
		"order": [[1, "asc"]],
		responsive: {
			details: {
				type: 'column',
				target: 'tr'
			}
		},
		searching: false,
		paginate: false,
		info: false,
	});

	// Click listener for the whole row to be clickable and toggle blocking/subscribing
	selectRows.each((index, elem) => {
		elem.addEventListener("click", (e) => {
			if (!selectTagsSet.has(e.target)) elem.firstElementChild.firstElementChild.click()
		});
	});
	
	// Select column with block and checkmark icons to select rows
	selectTags.each((index, elem) => {
		elem.addEventListener("click", function() {
			const mode = $('input[name="tag-mode"]:checked').val();
			const tag = elem.parentNode.nextElementSibling.firstElementChild;
			elem.toggleAttribute("checked");
			elem.classList.toggle("inactive");

			if (!swapping) {
				const isSelected = elem.hasAttribute("checked")
				if (mode == "block-mode") {
					if (isSelected) mutedTags.add(tag.innerHTML);
					else mutedTags.delete(tag.innerHTML);
				} else if (mode == "subscribe-mode") {
					if (isSelected) mutedTags.delete(tag.innerHTML);
					else mutedTags.add(tag.innerHTML);
				}
			}
			swapping = false;
		})
	});
	
	// Toggles visibility of tags based on tag mode change
	modeInput.change(function() {
		const mode = $('input[name="tag-mode"]:checked').val();
		selectTags.each((index, elem) => {
			if (mode == "block-mode") {
				elem.setAttribute("src", "/static/css/third-party/images/block.svg");
			} else if (mode == "subscribe-mode") {
				elem.setAttribute("src", "/static/css/third-party/images/check.svg");
			}
			swapping = true;
			elem.click()
		});
	});

	toggle_edit_emails();
	
	$('#ck-no-email').change(function() {
        toggle_edit_emails();      
    });
	
	
	edit_group_settings =
		function(params){
			const mode = $('input[name="tag-mode"]:checked').val();
			params.all_emails = $('#all-emails').is(":checked");
			params.digest = $('#digest-emails').is(":checked");
			params.no_emails = $('#no-emails').is(":checked");
			params.receive_attachments = $('#receive-attachments').is(":checked");
			params.upvote_emails = $('#upvote-emails').is(":checked");
			params.group_invite_emails = $('#group-invite-emails').is(":checked");
			params.admin_emails = $('#admin-emails').is(":checked");
			params.mod_emails = $('#mod-emails').is(":checked");
			params.muted_tags_data = JSON.stringify({ "muted_tags" : Array.from(mutedTags) });
			params.tag_blocking_mode = (mode === "block-mode") ? true : false
			$.post('/edit_group_settings', params, 
				function(res){
					notify(res, true);
				}
			);	
		};

		
	bind_buttons();
	
	function toggle_edit_emails() {
		no_emails = $('#ck-no-email').is(":checked");
		if (no_emails) {
			$('#edit-emails').css({"color": "gray"});
			$('#rdo-follow').attr('disabled', true);
			$('#rdo-no-follow').attr('disabled', true);
			$('#ck-upvote-emails').attr('disabled', true);
			$('#ck-upvote-emails').attr('checked', false);
			$('#ck-receive-attachments').attr('disabled', true);
			$('#ck-receive-attachments').attr('checked', false);
		} else {
			$('#edit-emails').css({"color": "black"});
			$('#rdo-follow').attr('disabled', false);
			$('#rdo-no-follow').attr('disabled', false);
			$('#ck-upvote-emails').attr('disabled', false);
			$('#ck-receive-attachments').attr('disabled', false);
		}
	}
			
	function bind_buttons() {
		var params = {'group_name': group_name};
 		
		var save_settings = bind(edit_group_settings, params);

		btn_save_settings.unbind("click");
		btn_cancel_settings.unbind("click");
        btn_save_settings.bind("click");
        btn_cancel_settings.bind("click");
        
		btn_save_settings.click(save_settings);
		
		btn_cancel_settings.click( function() {
			window.location = '/groups/' + params.group_name;
		});
		
	}
		
	$(".default-text").blur();
	tinyMCE.init({
		mode : "textareas",
		theme : "advanced",
		theme_advanced_buttons1 : "bold,italic,underline,strikethrough,|,justifyleft,justifycenter,justifyright,justifyfull,|,blockquote",
		theme_advanced_toolbar_location : "top",
		theme_advanced_toolbar_align : "left",
		theme_advanced_statusbar_location : "bottom",
		theme_advanced_resizing : true
	});


	// attach handlers to buttons 
	btn_add_dissimulate.click(function() {
		go_to('add_donotsend');
	});

	btn_delete_dissimulate.click(function() {
		if (confirm("Are you sure you want to delete the selected users from your do-not-send list?")) {
			var params = {'group_name' : group_name, 
							'toAdmin' : '',
							'toMod' : '',
							'toDelete' : get_selected('user').join(',')
						};
			post_edit_members(params);
		}
	});

	function get_selected(typeString) {
		var className = '.checkbox-' + typeString;
		var lists = [];
		$(className).each(function() {
			if (this.checked) lists.push(this.id);	
		});
		return lists;
	}

	function go_to(page) {
		window.location ='/groups/' + group_name + '/' + page;
	}

	var post_edit_members = function(params) {
		$.post('/edit_donotsend', params, function(res){
			notify(res,true);
			setTimeout(function(){
				window.location.reload();
			}, 400);
		});
	};
});


/* To avoid closure */	
function bind(fnc, val ) {
	return function () {
		return fnc(val);
	};
}

function notify(res, on_success){
	if(!res.status){
		noty({text: "Error: " + res.code, dismissQueue: true, timeout:2000, force: true, type: 'error', layout: 'topRight'});
	}else{
		if(on_success){
			noty({text: "Success!", dismissQueue: true, timeout:2000, force: true, type:'success', layout: 'topRight'});
		}
	}
}

// Updates UI based on saved user tag subscription settings
function getSavedTagSubscription() {
	const mode = $('input[name="tag-mode"]:checked').val();
	if (mode == "block-mode") {
		selectTags.each((index,elem) => {
			const tag = elem.parentNode.nextElementSibling.firstElementChild;
			if (mutedTags.has(tag.innerHTML)) {
				elem.toggleAttribute("checked");
				elem.classList.toggle("inactive");
			}
		})
	} else if (mode == "subscribe-mode") {
		selectTags.each((index,elem) => {
			const tag = elem.parentNode.nextElementSibling.firstElementChild;
			if (followedTags.has(tag.innerHTML)) {
				elem.toggleAttribute("checked");
				elem.classList.toggle("inactive");
			}
		})
	}
}
	
	
