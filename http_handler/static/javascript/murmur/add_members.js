$(document).ready(function(){
	
	var user_name = $.trim($('#user_email').text());
	var group_name = $.trim($("#group-name").text());
	
	var btn_add_members = $("#btn-add-members");
	
	add_members = 
		function(params){
			params.emails = $('#new-member-emails').val();
			$.post('/add_members', params, 
				function(res){
					if (res.status) {
						$('#new-member-emails').val("");
					}
					notify(res, true);
				}
			);	
		};
		
	bind_buttons();
			
	function bind_buttons() {
 		btn_add_members.unbind("click");
 		
 		btn_add_members.bind("click");
		var params = {'group_name': group_name};
 		
 		var add_mem = bind(add_members, params);
		
		btn_add_members.click(add_mem);
		
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
	
	
