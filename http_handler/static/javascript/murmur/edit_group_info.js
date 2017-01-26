$(document).ready(function(){

	var user_name = $.trim($('#user_email').text());
	var old_group_name = $.trim($("#group-name").text());

		var group_desc = $.trim($("#group-desc").text());

		var btn_save_settings = $("#btn-save-settings");
		var btn_cancel_settings = $("#btn-cancel-settings");

		edit_group_info=
			function(params){
				params.old_group_name = old_group_name;
				params.new_group_name = $("#edit-group-name").val();
				params.group_desc = $("#edit-group-description").val();
				params.public = $('input[name=pubpriv]:checked', "#group-info-form").val();
				params.attach = $('input[name=attach]:checked', "#group-info-form").val();

				$.post('/edit_group_info', params,
					function(res){
						notify(res,true);
						if (res.status) {
							window.location = "/groups/" + params.new_group_name + "/edit_group_info";
						}
						
					}
				);
			};

	    bind_buttons();

		function bind_buttons() {
		var params = {'old_group_name': old_group_name };
		btn_save_settings.unbind("click");
		btn_cancel_settings.unbind("click");
        btn_save_settings.bind("click");
        btn_cancel_settings.bind("click");


		var save_settings = bind(edit_group_info, params);
		btn_save_settings.click(save_settings);
		
		btn_cancel_settings.click( function() {
			window.location = '/groups/' + params.old_group_name;
		});
		
			}

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
	