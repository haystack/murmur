$(document).ready(function(){
	
	var group_name = $.trim($("#group-name").text());
	var btn_add_list = $("#btn-add-list");
	
	add_list = 
		function(params){
			params = {
				'group_name' : params.group_name,
				'email' : $('#new-list-email').val(),
				'can_receive' : $('#can_receive').prop('checked'),
				'can_post' : $('#can_post').prop('checked'),
				'list_url' : $('#new-list-url').val()
			}

			$.post('/add_list', params, 
				function(res){
					if (res.status) {
						$('#new-list-url').val("");
						$('#new-list-email').val("");
						$('#can_receive').prop('checked', false);
						$('#can_post').prop('checked', false);
					}
					notify(res, true);
				}
			);	
		};
		
	bind_buttons();
			
	function bind_buttons() {
 		btn_add_list.unbind("click");
 		
 		btn_add_list.bind("click");
		var params = {'group_name': group_name, 'user_email' : user_name};
 		
 		var add_l = bind(add_list, params);
		
		btn_add_list.click(add_l);
		
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