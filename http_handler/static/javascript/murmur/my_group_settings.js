$(document).ready(function(){
	
	var user_name = $.trim($('#user_email').text());
	var group_name = $.trim($("#group-name").text());
	
	var btn_add_dissimulate = $("#btn-add-dissimulate"),
		btn_delete_dissimulate = $("#btn-delete-dissimulate");

	var btn_save_settings = $("#btn-save-settings");
	var btn_cancel_settings = $("#btn-cancel-settings");
	
	var donotsend_members_table = $('#donotsend-members-table').dataTable({
		"columns": [ { 'orderable': false}, null],
		"order": [[1, "asc"]],
		responsive: true
	});

	toggle_edit_emails();
	
	$('#ck-no-email').change(function() {
        toggle_edit_emails();      
    });
	
	
	edit_group_settings =
		function(params){
			params.upvote_emails = $('#ck-upvote-emails').is(":checked");
			params.receive_attachments = $('#ck-receive-attachments').is(":checked");
			params.no_emails = $('#ck-no-email').is(":checked");
			params.following = $('input[name=following]:checked', '#group-settings-form').val();
			params.digest = $('#ck-digest').is(":checked");
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
			console.log("deleted")
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
	
	
