$(document).ready(function(){ 
	/* Dynamic Table Definitions */	
	
	groups_table = $('#groups-table').dataTable({
		"sDom": '<"top"f<"clear">>rt<"bottom"ilp<"clear">>',
		"bPaginate": false,
		"bInfo": false,
		"bAutoWidth": false,
		"bFilter": false,
		"sWidth": "100%",
		"aaSorting": [],
		"aoColumns": [                 
			{"bSortable": false, "sWidth": "100%"}
		]  
	});
	
	posts_table = $('#posts-table').dataTable({
		"sDom": '<"top"f<"clear">>rt<"bottom"ilp<"clear">>',
		"bPaginate": false,
		"bInfo": false,
		"bAutoWidth": false,
		"bFilter": false,
		"sWidth": "100%",
		"aaSorting": [],
		"aoColumns": [                 
			{"bSortable": false, "sWidth": "100%"}
		]  
	});
	
	members_table = $('#members-table').dataTable({
		"sDom": '<"top"f<"clear">>rt<"bottom"ilp<"clear">>',
		"bPaginate": false,
		"bInfo": false,
		"bAutoWidth": false,
		"bFilter": false,
		"sWidth": "100%",
		"aoColumns": [                 
			{"bSortable": false, "sWidth": "50%"},
			{"bSortable": false, "sWidth": "10%"},
			{"bSortable": false, "sWidth": "10%"},
			{"bSortable": false, "sWidth": "10%"},
			{"bSortable": false, "sWidth": "10%"},
			{"bSortable": false, "sWidth": "10%"}
		]  
	});
	
	
	
	/* Default blur effect in textbox */
	
	$(".default-text").focus(function(srcc)
	{
	    if ($(this).val() == $(this)[0].title)
	    {
	        $(this).removeClass("default-text-active");
	        $(this).val("");
	    }
	});
    
	$(".default-text").blur(function()
	{
	    if ($(this).val() == "")
	    {
	        $(this).addClass("default-text-active");
	        $(this).val($(this)[0].title);
	    }
	});
	
    
	
	
	/* All Group related AJAX calls */	
	list_groups = 
		function(params){
			$.post('list_groups', params, 
				function(res){
					populate_groups_table(res);
				}
			);	
		}
	
	
	
	group_info = 
		function(params){
			$.post('group_info', params, 
				function(res){
					populate_group_info(res);
					populate_members_table(res);
					highlight_table_row(groups_table, params.curr_row);
					notify(res, false);
				}
			);	
		}
	
	
	create_group = 
		function(params){
			params.group_name = $("#text-create-group").val()
			$.post('create_group', params, 
				function(res){
					$("#text-create-group").val("");
					$("#text-create-group").blur();
					list_groups(params);
					notify(res, true);
				}
			);	
		}

	subscribe_group = 
		function(params){
			$.post('subscribe_group', params, 
				function(res){
					group_info(params)
					notify(res, true);
				}
			);	
		}
		
		
	unsubscribe_group = 
		function(params){
			$.post('unsubscribe_group', params, 
				function(res){					
					group_info(params)
					notify(res, true);
				}
			);	
		}

	activate_group = 
		function(params){
			$.post('activate_group', params, 
				function(res){
					group_info(params);
					notify(res, true);
				}
			);	
		}
		
	
	deactivate_group = 
		function(params){
			$.post('deactivate_group', params, 
				function(res){
					group_info(params);
					notify(res, true);
				}
			);	
		}				  
		
	/* All Post related AJAX calls */	
	list_posts = 
		function(params){
			$.post('list_posts', params, 
				function(res){
					populate_posts_table(res);
				}
			);	
		}
	
	load_post = 
		function(params){
			render_post(params);
			highlight_table_row(posts_table, params.curr_row);
		}
	
	follow_thread = 
		function(params){
			$.post('follow_thread', {'requester_email': params.requester_email, 
						  'thread_id': params.thread_id,
						  'msg_id': params.msg_id
					  	}, 
				function(res){
					notify(res, true);
				}
			);	
		}
	
	unfollow_thread = 
		function(params){
			$.post('unfollow_thread', {'requester_email': params.requester_email, 
						  'thread_id': params.thread_id,
						  'msg_id' : params.msg_id
					  	}, 
				function(res){
					notify(res, true);
				}
			);	
		}
		
	insert_post = 
		function(params){
			$.post('insert_post', params, 
				function(res){
					notify(res, false);
				}
			);	
		}
	
	insert_reply = 
		function(params){
			params.msg_text = $("#reply-text-input").val() + '<br />' + params.text;
			params.poster_email = params.requester_email;
			delete params.requester_email;
			delete params.text;
			$.post('insert_reply', params, 
				function(res){
					if(res.status){
						$("reply-text-input").val="";
						$("reply-text-input").blur();
					}
					notify(res, true);
				}
			);	
		}		

	/* To avoid closure */	
	function bind(fnc, val ) {
		return function () {
			return fnc(val);
		};
	}

	function populate_groups_table(res){
		groups_table.fnClearTable();
		if(res.status){
			var params = {'requester_email': res.user};
	 		$("#btn-create-group").unbind("click");
	 		$("#btn-create-group").bind("click");
			var crt_group = bind(create_group, params);
			$("#btn-create-group").click(crt_group);
			for(var i = 0; i< res.groups.length; i++){
				curr = groups_table.fnAddData( [
									'<span class="strong">' + res.groups[i].name + '</span>'
								  ]);
				var params = {'requester_email': res.user, 
							  'group_name': res.groups[i].name,
							  'curr_row': curr
							 }
				var f = bind(group_info, params)
				curr_row = groups_table.fnGetNodes(curr);
				$(curr_row).click(f);
			}
		}
		groups_table.fnGetNodes(0).click();
	}
	
	function populate_members_table(res){
		members_table.fnClearTable();
		for(var i = 0; i< res.members.length; i++){
			curr = members_table.fnAddData( [
								res.members[i].email,
								res.members[i].active,
								res.members[i].admin,
								res.members[i].moderator,
								res.members[i].member,
								res.members[i].guest
							  ]);
		}
		
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
	
	function populate_group_info(res, curr_row){
		var info = "<h3>Group Info</h3><hr />";
		info += '<span class="strong">Group Name: </span><span class="strong-gray">' + res.group_name + '</span><br />';
		info += '<span class="strong">Active: </span><span class="strong-gray">' + res.active + '</span><br /> <br />';
		$("#group-info").html(info);
		$('#group-display-area').show();
		var params = {'requester_email': res.user, 
					  'group_name': res.group_name,
					  'curr_row': curr_row
					 }
 		$("#btn-activate-group").unbind("click");
 		$("#btn-deactivate-group").unbind("click");
 		$("#btn-subscribe-group").unbind("click");
 		$("#btn-unsubscribe-group").unbind("click");
 		$("#btn-activate-group").bind("click");
 		$("#btn-deactivate-group").bind("click");
 		$("#btn-subscribe-group").bind("click");
 		$("#btn-unsubscribe-group").bind("click");
		var act_group = bind(activate_group, params);
		var deact_group = bind(deactivate_group, params);
		var sub_group = bind(subscribe_group, params);
		var unsub_group = bind(unsubscribe_group, params);
		$("#btn-activate-group").click(act_group);
		$("#btn-deactivate-group").click(deact_group);
		$("#btn-subscribe-group").click(sub_group);
		$("#btn-unsubscribe-group").click(unsub_group);
	}
	
	
	
	function populate_posts_table(res){
		posts_table.fnClearTable();
		if(res.status){
			var params = {'requester_email': res.user};
			for(var i = 0; i< res.threads.length; i++){
				curr = posts_table.fnAddData( [
									'<span class="strong">' + res.threads[i].post.from + '</span><br /><span class="strong-gray ellipsis">' + res.threads[i].post.subject + '</span>'
								  ]);
				var params = {'requester_email': res.user,
							  'thread_id' : res.threads[i].thread_id, 
							  'post': res.threads[i].post,
							  'replies' : res.threads[i].replies,
							  'curr_row': curr
							 }
				var f = bind(load_post, params)
				curr_row = posts_table.fnGetNodes(curr);
				$(curr_row).click(f);
			}
		}
		//posts_table.fnGetNodes(0).click();
	}
	
	
	function render_post(res){
		var content = '<div class="main-area-content">';
		content += '<div><div style="float:right"><button type="button" id="btn-follow" style="margin-top:10px;">Follow</button> <button type="button" id="btn-unfollow" style="margin-top:10px;">Unfollow</div> <div><h3>' + res.post.subject + '</h3>' + '<span class="strong">From: </span> <span class="strong-gray">' + res.post.from + '</span><br /><span class="strong">To: </span><span class="strong-gray">' + res.post.to + '</span></div> </div> <hr />' + res.post.text;
		content += '<div class="reply">'
		for(var i = 0; i< res.replies.length; i++){
                       content += '<div class="main-area-content">';
                       content += '<span class="strong-gray">' + res.replies[i].from + '</span><br /><br />' + res.replies[i].text;

                       content += '</div>'
                               
               }
		content += '</div>';
		$("#main-area").empty();
                $("#main-area").html(content);
		var content = '<div class="main-area-content">';
		
		content += '<div class="comment"><textarea id="reply-text-input"></textarea><button type="button" id="btn-reply" style="margin-top:10px;">Reply</button></div>';
		 
		content += '</div>'	
		$("#main-area").append(content);
		var params = {'requester_email': res.requester_email, 
					  'thread_id': res.thread_id,
					  'msg_id':res.post.msg_id,
					  'group_name': res.post.to,
					  'subject': res.post.subject,
					  'text':res.post.text
					}
		$("#btn-reply").unbind("click");
		$("#btn-follow").unbind("click");
		$("#btn-unfollow").unbind("click");
		$("#btn-reply").bind("click");
		$("#btn-follow").bind("click");
		$("#btn-unfollow").bind("click");
		var ins_reply = bind(insert_reply, params);
		var flw_thread = bind(follow_thread, params);
		var unflw_thread = bind(unfollow_thread, params);
		$("#btn-reply").click(ins_reply);
		$("#btn-follow").click(flw_thread);
		$("#btn-unfollow").click(unflw_thread);
	  		
        
	}
	
	
	
	function highlight_table_row(table, curr_row){
		if(curr_row !== undefined){
			$('td', table.fnGetNodes()).css("background-color","white");
			$('td', table.fnGetNodes(curr_row)).css("background-color","lightyellow");
		}	
	}
	
	
	
	
	/* Handle based on URLs */
	
	if(window.location.pathname.indexOf('/groups')!=-1){
		list_groups();
	}else{
		/*
		$.post('list_groups', {}, 
			function(res){
				for(var i = 0; i< res.groups.length; i++){
					$("#list-create-group").append($("<option></option>")
         		   .attr("value", res.groups[i].name)
         		   .text(res.groups[i].name)); 
					
				}
			} 
		);
		*/
		list_posts();	
		//setInterval(list_posts, 10000);
	}
	$(".default-text").blur();
});

				
	




