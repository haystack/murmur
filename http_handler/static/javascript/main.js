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
					populate_posts_table(res, params);
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
			params.msg_text = $("#new-post-text").val();
                        params.subject = $("#new-post-subject").val();
                        params.group_name = $("#new-post-to").val();
                        params.poster_email = params.requester_email;
			$.post('insert_post', params, 
				function(res){
					if(res.status){
                                        	list_posts({'load':true, 'thread_id':res.thread_id});
					}
					notify(res, true);
				}
			);	
		}
	
	insert_reply = 
		function(params){
			params.msg_text = $("#reply-text-input").val() + '<br /> <br /> On ' + new Date() + ', <a href="mailto:' + params.from + '">' + params.from + '</a> wrote: <br />' + '<blockquote style="margin: 0 0 0 0.8ex; border-left: 1px #ccc solid; padding-left: 1ex;">' + params.text + '</blockquote>';
			if(params.subject.substr(0,3).trim().toLowerCase() != 're:'){
				params.subject = 'Re: ' + params.subject;
			}
			params.poster_email = params.requester_email;
			delete params.requester_email;
			delete params.text;
			$.post('insert_reply', params, 
				function(res){
					if(res.status){
						list_posts({'load':true, 'thread_id':res.thread_id});
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
	
	
	
	function populate_posts_table(res, load_params){
		posts_table.fnClearTable();
		var active_row = 0
		if(res.status){
			var params = {'requester_email': res.user};
			for(var i = 0; i< res.threads.length; i++){
				d = format_date(new Date(res.threads[i].timestamp));
				var content = '<div class="left-column-area-metadata">';
				content += '<span class="gray ellipsis">' + d.date + '</span>';
				content += '<span class="gray ellipsis">' + d.time + '</span>';
				content += '<span class="unread">' + res.threads[i].replies.length + '</span> <br />';
				content += '</div>'
				content += '<div class= "left-column-area-content">';
				content +=  '<span class="strong ellipsis">' + res.threads[i].post.subject + '</span>'
				content += '<span class="strong-gray ellipsis">' + res.threads[i].post.from + '</span>';
				content += '<span class="blurb ellipsis">' + strip(res.threads[i].post.text) + '</span>';
				content += '</div>'
				
				curr = posts_table.fnAddData( [
								content	  
								]);
				var params = {'requester_email': res.user,
							  'thread_id' : res.threads[i].thread_id, 
							  'post': res.threads[i].post,
							  'replies' : res.threads[i].replies,
							  'curr_row': curr
							 }
				var f = bind(load_post, params)
				curr_row = posts_table.fnGetNodes(curr);
				if(res.threads[i].thread_id == load_params.thread_id){
					active_row = curr;
					console.debug("new post/reply (thread-id: " + load_params.thread_id +").");
				}

				$(curr_row).click(f);
			}
		}
		if(load_params.load == true){
			posts_table.fnGetNodes(active_row).click();
			console.debug("load = true");
		}
	}
	
	
	function render_post(res){
		var content = '<div class="main-area-content">';
		content += '<div>';
		content += '<div style="float:right">';
		content += '<button type="button" id="btn-follow" style="margin:5px;">Follow</button>';
		content += '<button type="button" id="btn-unfollow" style="margin:5px;">Unfollow</button>';
		content += '</div>';
		content += '<div>';
		content += '<h3>' + res.post.subject + '</h3>'
		content += '<span class="strong">From: </span> <span class="strong-gray">' + res.post.from + '</span><br />';
		content += '<span class="strong">To: </span><span class="strong-gray">' + res.post.to + '</span> <br />';
		content += '<span class="strong">Date: </span><span class="strong-gray">' + new Date(res.post.timestamp) + '</span>';
		content += '</div>';
		content += '</div>';
		content += '<hr />';
		content += res.post.text;
		content += '<div class="reply">'
		for(var i = 0; i< res.replies.length; i++){
                       	content += '<div class="main-area-content">';
			content += '<span class="strong">' + res.replies[i].from + '</span>&nbsp;';
                       	content += 'on ' + new Date(res.replies[i].timestamp) + '&nbsp;';
			content += '<br /><br />';
		      	content +=  res.replies[i].text;
                       	content += '</div>'
                               
               }
		content += '</div>';
		content += '<div class="main-area-content">';	
		content += '<div class="comment"><textarea id="reply-text-input"></textarea><button type="button" id="btn-reply" style="margin-top:10px;">Reply</button></div>';
		content += '</div>'; 
		content += '</div>'	
		$("#main-area").empty();
                $("#main-area").html(content);
		//tinyMCE.execCommand('mceAddControl', false, 'reply-text-input');
		var params = {'requester_email': res.requester_email, 
					  'thread_id': res.thread_id,
					  'msg_id':res.post.msg_id,
					  'from':res.post.from,
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
	
	function new_post(res){
                var content = '<div class="main-area-content">';
                content += '<div class="comment">';
		content += '<span class="strong">To : </span>'
		content += '<select id="new-post-to"></select> <br />';
		content += '<span class="strong">Subject : </span> <br />';
                content += '<input id="new-post-subject" type="text" style="width: 100%; box-sizing: border-box;"></input> <br /> <br />';
		content += '<textarea id="new-post-text" style="height:150px;"></textarea>';
		content += '<button type="button" id="btn-post" style="margin-top:10px;">Post</button>'
		content += '</div>';

                content += '</div>'
                $("#main-area").html(content);
		for(var i = 0; i< res.groups.length; i++){
			$("#new-post-to").append($("<option></option>")
         		   .attr("value", res.groups[i].name)
         		   .text(res.groups[i].name)); 
					
		
		}
		params = {'requester_email':res.user};
		var ins_post = bind(insert_post, params);
		$("#btn-post").unbind("click");
                $("#btn-post").bind("click");
		$("#btn-post").click(ins_post);
	}
	
	function highlight_table_row(table, curr_row){
		if(curr_row !== undefined){
			table.active_row = curr_row;
			$('td', table.fnGetNodes()).css("background-color","white");
			$('td', table.fnGetNodes(curr_row)).css("background-color","lightyellow");
		}	
	}
	
	
	function strip(html){
   		var tmp = document.createElement("DIV");
   		tmp.innerHTML = html;
   		var txt = tmp.textContent||tmp.innerText;
		return txt.substring(0, 100);
	}


	function format_date(d) {
		var dateStr,hours,minutes,ampm;
		dateStr = (d.getMonth() + 1) +'/'+d.getDate()+'/'+d.getFullYear();
		hours = d.getHours();
		minutes = d.getMinutes();
		ampm = hours >= 12 ? 'PM' : 'AM';
		hours = hours % 12;
		if(!hours) {
			hours = 12;
		}
		//hours = hours ? hours : 12;
		minutes = minutes < 10 ? '0'+minutes : minutes;
		timeStr = hours + ':' + minutes + ' ' + ampm;
		return {'date':dateStr, 'time': timeStr}
	}


	 function init_posts_page (){
		$.post('list_groups', {},
                        function(res){
                                $("#btn-create-new-post").unbind("click");
                                var func_new_post = bind(new_post, res);
                                $("#btn-create-new-post").bind("click");
                                $("#btn-create-new-post").click(func_new_post);

                        }
                );
		list_posts({'load':false});
	}
	
	
	/* Handle based on URLs */
	
	if(window.location.pathname.indexOf('/groups')!=-1){
		list_groups();
	}else{
		init_posts_page();	
		//setInterval(refresh, 10000);
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
