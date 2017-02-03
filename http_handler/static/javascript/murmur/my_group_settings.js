$(document).ready(function(){
	
	var user_name = $.trim($('#user_email').text());
	var group_name = $.trim($("#group-name").text());
	
	var btn_save_settings = $("#btn-save-settings");
	var btn_cancel_settings = $("#btn-cancel-settings");
	
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
	
	
