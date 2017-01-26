$(document).ready(function(){
	
	var user_name = $.trim($('#user_email').text());
	
	var btn_create_group = $("#btn-new-create-group");
	
	create_group = 
		function(params){
			params.group_name = $("#new-group-name").val();
			params.group_desc = $("#new-group-description").val();
			params.public = $('input[name=pubpriv]:checked', '#new-group-form').val();
			params.attach = $('input[name=attach]:checked', '#new-group-form').val();
			$.post('create_group', params, 
				function(res){
					notify(res, true);
					if(res.status){
						window.location = '/groups/' + params.group_name;
					}
				}
			);	
		};
		
	bind_buttons();
			
	function bind_buttons() {
 		btn_create_group.unbind("click");
 		
 		btn_create_group.bind("click");
		var params = {};
 		
 		var add_group = bind(create_group, params);
		
		btn_create_group.click(add_group);
		
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
	
	
