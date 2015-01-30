$(document).ready(function(){
	
	CKEDITOR.replace( 'reply-text-input' );
	
	var gmail_quotes = $(".gmail_quote");
    var check = "---------- Forwarded message ----------";
	
    gmail_quotes.each(function () {
    	var text = $(this).text();
    	
    	if (text.substring(0, check.length) !== check) {
    		$(this).wrap( "<div class='accordian'></div>" );
    	}
    });
    
    
 //   var block = $( ".moz-cite-prefix" ).next();
 //   block.addClass("moz-blockquote");
 //   $(".moz-cite-prefix, .moz-blockquote").wrapAll( "<div class='accordian'><div></div></div>" );
    
    $(".accordian").prepend("<h3>...</h3>");
    
	$(".accordian").accordion({collapsible: true, 
							   active: false,
							   heightStyle: "content"});
							   

	var requester_email = $("#user_email").text();
	var params = {'requester_email': requester_email, 
				  'thread_id': getParameterByName('tid'),
				  'msg_id': $("#post_info").val(),
				  'from': $("#post-from").text(),
				  'group_name': getParameterByName('group_name'),
				  'subject': $("#post-subject").text(),
			};
	   
	$("#btn-reply").unbind("click");
	$("#btn-follow").unbind("click");
	$("#btn-unfollow").unbind("click");
	$("#btn-reply").bind("click");
	$("#btn-follow").bind("click");
	$("#btn-unfollow").bind("click");

	insert_reply = 
		function(params){
			params.msg_text = CKEDITOR.instances['reply-text-input'].getData();
			if(params.subject.substr(0,3).trim().toLowerCase() != 're:'){
				params.subject = 'Re: ' + params.subject;
			}
			params.poster_email = params.requester_email;
			$.post('insert_reply', params, 
				function(res){
					if(res.status){
						window.location.reload();
					}
					notify(res, true);
				}
			);	
		};	
	
	follow_thread = 
		function(params){
			$.post('follow_thread', {'requester_email': params.requester_email, 
						  'thread_id': params.thread_id,
						  'msg_id': params.msg_id
					  	}, 
				function(res){
					if(res.status){
						$("#btn-follow").hide();
	            				$("#btn-unfollow").show();
					}
					notify(res, true);
				}
			);	
		};
	
	unfollow_thread = 
		function(params){
			$.post('unfollow_thread', {'requester_email': params.requester_email, 
						  'thread_id': params.thread_id,
						  'msg_id' : params.msg_id
					  	}, 
				function(res){
					if(res.status){
	                   $("#btn-follow").show();
	                   $("#btn-unfollow").hide();
	                }
					notify(res, true);
				}
			);	
		};		
		
	var ins_reply = bind(insert_reply, params);
	var flw_thread = bind(follow_thread, params);
	var unflw_thread = bind(unfollow_thread, params);	
		
	$("#btn-reply").click(ins_reply);
	$("#btn-follow").click(flw_thread);
	$("#btn-unfollow").click(unflw_thread);
		
	$("#btn-follow").hide();
	$("#btn-unfollow").hide();
	
	
	
	var f_list = $.parseJSON($("#flist").val());
	if (f_list && f_list.indexOf(requester_email) != -1) {
		$("#btn-unfollow").show();
	} else {
		$("#btn-follow").show();
	}  	
});

function getParameterByName(name) {
    name = name.replace(/[\[]/, "\\[").replace(/[\]]/, "\\]");
    var regex = new RegExp("[\\?&]" + name + "=([^&#]*)"),
        results = regex.exec(location.search);
    return results === null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
}

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
	
	
