$(document).ready(function(){
	
	CKEDITOR.replace( 'new-post-text' );
	
	var user_name = $.trim($('#user_email').text());
	
	var post = $("#btn-post");
	
	insert_post = 
		function(params){
			params.msg_text = CKEDITOR.instances['new-post-text'].getData();
            params.subject = $("#new-post-subject").val();
			params.group_name = $("#new-post-to").text();
			params.friendly_name = $("#friendly-group-name").text();
            params.poster_email = params.requester_email;
			$.post('/insert_post', params, 
				function(res){
					notify(res, true);
					
					if(res.status){
						setTimeout(function () {
                    		window.location.href = "/post_list?group_name=" + params.group_name;
                  		}, 600);
					}
				}
			);	
		};
		
	bind_buttons();

	function bind_buttons() {
 		post.unbind("click");
 		
 		post.bind("click");
		var params = {'requester_email': user_name};
 		
 		var add_post = bind(insert_post, params);
		
		post.click(add_post);
		
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
	
	
