$(document).ready(function(){
	/* Global Objects */

	posts_local_data = {};

	groups_local_data = {};

 
	/* Dynamic Table Definitions */	
	
	members_table = $('#members-table').dataTable({
		"sDom": '<"top"f<"clear">>rt<"bottom"ilp<"clear">>',
		"bPaginate": false,
		"bInfo": false,
		"bAutoWidth": false,
		"bFilter": false,
		"sWidth": "100%",
		"aoColumns": [                 
			{"bSortable": false, "sWidth": "50%"},
			{"bSortable": false, "sWidth": "12.5%"},
			{"bSortable": false, "sWidth": "12.5%"},
			{"bSortable": false, "sWidth": "12.5%"},
			{"bSortable": false, "sWidth": "12.5%"}
		]  
	});
	
	
	
	/* Default blur effect in textbox */
	
	$(".default-text").focus(function(src)
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
			$.ajax({
				type: 'POST',
				url: 'list_groups', 
				data: params,
				success:  function(res){
					populate_groups_table(res);
				},
				async: false,
			});	
	};
	
	
	
	group_info = 
		function(params){
			$.post('group_info', params, 
				function(res){
					$("#new-group-area").hide();
					populate_group_info(res);
					populate_members_table(res);
					groups_local_data.selected_group = params.group_name;
            		$('.row-item').css("background-color","white");
            		$('#' + params.group_name).css("background-color","lightyellow");
					notify(res, false);
				}
			);	
		};
	
	
	create_group = 
		function(params){
			params.group_name = $("#new-group-name").val();
			params.public = $('input[name=pubpriv]:checked', '#new-group-form').val();
			$.post('create_group', params, 
				function(res){
					list_groups(params);
					group_info(params);
					notify(res, true);
				}
			);	
		};
		
	add_members = 
		function(params){
			params.emails = $('#new-member-emails').val();
			$.post('add_members', params, 
				function(res){
					list_groups(params);
					group_info(params);
					notify(res, true);
				}
			);	
		};

	subscribe_group = 
		function(params){
			$.post('subscribe_group', params, 
				function(res){
					list_groups(params);
					group_info(params);
					notify(res, true);
				}
			);	
		};
		
		
	unsubscribe_group = 
		function(params){
			$.post('unsubscribe_group', params, 
				function(res){
					list_groups(params);
					group_info(params);
					notify(res, true);
				}
			);	
		};

	activate_group = 
		function(params){
			$.post('activate_group', params, 
				function(res){
					group_info(params);
					notify(res, true);
				}
			);	
		};
		
	
	deactivate_group = 
		function(params){
			$.post('deactivate_group', params, 
				function(res){
					group_info(params);
					notify(res, true);
				}
			);	
		};			  
		
	/* All Post related AJAX calls */	
	list_posts = 
		function(params){
			$.post('list_posts', params, 
				function(res){
					populate_posts_table(res, params, true);
				}
			);	
		};
	
	
	refresh_posts =
    	function(){
			if(posts_local_data.timestamp != null){
				params = {'timestamp': 		posts_local_data.timestamp,
						  'active_group': 	$("#active_group").text()
						 };
            	$.post('refresh_posts', params,
                function(res){
					if(res.status && res.threads.length > 0){
                    	populate_posts_table(res, {}, false);
					}
                });
			}
    };



	load_post = 
		function(params){
			render_post(params);
			posts_local_data.selected_thread = params.thread_id;
			$('.row-item').css("background-color","white");
			$('#' + params.thread_id).css("background-color","lightyellow");
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
		
	insert_post = 
		function(params){
			params.msg_text = $("#new-post-text").val();
                        params.subject = $("#new-post-subject").val();
                        params.group_name = $("#new-post-to").text();
                        params.poster_email = params.requester_email;
			$.post('insert_post', params, 
				function(res){
					if(res.status){
                    	list_posts({'load':true, 
                    				'active_group': params.group_name,
                    				'thread_id':res.thread_id});
					}
					notify(res, true);
				}
			);	
		};
	
	insert_reply = 
		function(params){
			params.msg_text = $("#reply-text-input").val();
			if(params.subject.substr(0,3).trim().toLowerCase() != 're:'){
				params.subject = 'Re: ' + params.subject;
			}
			params.poster_email = params.requester_email;
			delete params.text;
			$.post('insert_reply', params, 
				function(res){
					if(res.status){
						list_posts({'load':true, 
									'active_group': params.group_name,
									'thread_id':res.thread_id});
					}
					notify(res, true);
				}
			);	
		};		

	/* To avoid closure */	
	function bind(fnc, val ) {
		return function () {
			return fnc(val);
		};
	}

	function populate_groups_table(res){
		var groups_table = $("#groups-table");
		groups_table.html("");
		if(res.status){
	 		
	 		$("#btn-create-group").unbind("click");
	 		$("#btn-create-group").bind("click");
	 		
	 		var crt_group = bind(new_group, res);
	 		
			$("#btn-create-group").click(crt_group);
			
			
			for(var i = 0; i< res.groups.length; i++){
				var content = '<li class="row-item" id="'+ res.groups[i].name+'">';
				content += '<span class="strong">' + res.groups[i].name + '</span>';
				if (res.groups[i].member == true)
					content += '<span class="member label">Member</span>';
				
				if (res.groups[i].admin == true)
					content += '<span class="admin label">Admin</span>';
				
				if (res.groups[i].mod == true)
					content += '<span class="mod label">Mod</span>';
				
				content += '</li>';
				var curr_row = $(content);
				groups_table.append(curr_row);
								 
				var params = {'requester_email': res.user, 
						'group_name': res.groups[i].name
					};
				var f = bind(group_info, params);
				
				curr_row.on('click',f);
			}
		}
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
		var info = "<h3>Group: " + res.group_name + "</h3><hr />";
		info += '<span class="strong">Active: </span><span class="strong-gray">' + res.active + '</span><br /> <br />';
		info += '<a href="/posts?group_name=' + res.group_name + '">View Posts</a> <br /> <br />';
		$("#group-info").html(info);
		$('#group-display-area').show();
		var params = {'requester_email': res.user, 
					  'group_name': res.group_name,
					  'curr_row': curr_row
					};
 		$("#btn-activate-group").unbind("click");
 		$("#btn-deactivate-group").unbind("click");
 		$("#btn-subscribe-group").unbind("click");
 		$("#btn-unsubscribe-group").unbind("click");
 		$("#btn-add-members").unbind("click");
 		
 		$("#btn-activate-group").bind("click");
 		$("#btn-deactivate-group").bind("click");
 		$("#btn-subscribe-group").bind("click");
 		$("#btn-unsubscribe-group").bind("click");
 		$("#btn-add-members").bind("click");
 		
		var act_group = bind(activate_group, params);
		var deact_group = bind(deactivate_group, params);
		var sub_group = bind(subscribe_group, params);
		var unsub_group = bind(unsubscribe_group, params);
		var ad_members = bind(add_new_members, params);
		
		$("#btn-activate-group").click(act_group);
		$("#btn-deactivate-group").click(deact_group);
		$("#btn-subscribe-group").click(sub_group);
		$("#btn-unsubscribe-group").click(unsub_group);
		$("#btn-add-members").click(ad_members);
		
		$("#btn-subscribe-group").hide();
		$("#btn-unsubscribe-group").hide();
		$("#btn-activate-group").hide();
		$("#btn-deactivate-group").hide();
		$("#btn-add-members").hide();
		
		if(res.admin){
			if(res.active){
				$("#btn-deactivate-group").show();
				
			} else{
				$("#btn-activate-group").show();
			}
			$("#btn-add-members").show();
		}
		if(res.active){
			if(res.subscribed){
                    $("#btn-unsubscribe-group").show();
            } else{
                    $("#btn-subscribe-group").show();
            }
	
		}

	}
	
	
	
	function populate_posts_table(res, load_params, reset){
		var posts_table = $("#posts-table"); 
		if(reset == true){
			posts_table.empty();
		}
		var selected_thread = posts_local_data.selected_thread;
		timestamp = new Date(0);
		if(res.status){
			var params = {'requester_email': res.user};
			for(var i = 0; i< res.threads.length; i++){
				d = format_date(new Date(res.threads[i].timestamp));
				var content = '<div class="left-column-area-metadata">';
				content += '<span class="gray ellipsis">' + d.date + '</span>';
				content += '<span class="gray ellipsis">' + d.time + '</span>';
				content += '<span class="unread">' + res.threads[i].replies.length + '</span> <br />';
				content += '</div>';
				content += '<div class= "left-column-area-content">';
				content +=  '<span class="strong ellipsis">' + res.threads[i].post.subject + '</span>';
				content += '<span class="strong-gray ellipsis">' + res.threads[i].post.from + '</span>';
				content += '<span class="blurb ellipsis">' + res.threads[i].post.text + '</span>';
				content += '</div>';
				var curr_row = $('<li class="row-item" id="' + res.threads[i].thread_id + '">' + content + '</li>');
				var params = {'requester_email': res.user,
						'thread_id' : res.threads[i].thread_id, 
						 'post': res.threads[i].post,
						 'replies' : res.threads[i].replies,
						 'f_list' : res.threads[i].f_list
					};
				var f = bind(load_post, params);
				if(res.threads[i].thread_id == load_params.thread_id){
					selected_thread = res.threads[i].thread_id;
					console.debug("new post/reply (thread-id: " + load_params.thread_id +").");
				}
				if(new Date(res.threads[i].timestamp) > timestamp){
                                        timestamp = res.threads[i].timestamp;
                                }

				curr_row.on('click',f);
				
				if(reset){
					posts_table.append(curr_row);
				}else{
					var row = $('#' + res.threads[i].thread_id);
					if(row.length == 0){ 
						posts_table.prepend(curr_row);
					}else{
						posts_table.prepend(curr_row);
						row.remove();
						if(res.threads[i].thread_id == posts_local_data.selected_thread){
							curr_row.click();
						}
					}	
				}
			

			}
		}
		if(load_params.load == true){
			posts_table.find('"#'+selected_thread+'"').click();
			console.debug("load = true");
		}
		posts_local_data.timestamp = timestamp;
	}
	
	
	function render_post(res){
		var content = '<div class="main-area-content">';
		content += '<div>';
		content += '<div style="float:right">';
		content += '<button type="button" id="btn-follow" style="margin:5px;">Follow</button>';
		content += '<button type="button" id="btn-unfollow" style="margin:5px;">Unfollow</button>';
		content += '</div>';
		content += '<div>';
		content += '<h3>' + res.post.subject + '</h3>';
		content += '<span class="strong">From: </span> <span class="strong-gray">' + res.post.from + '</span><br />';
		content += '<span class="strong">To: </span><span class="strong-gray">' + res.post.to + '</span> <br />';
		content += '<span class="strong">Date: </span><span class="strong-gray">' + new Date(res.post.timestamp) + '</span>';
		content += '</div>';
		content += '</div>';
		content += '<hr />';
		content += res.post.text;
		content += '<div class="reply">';
		for(var i = 0; i< res.replies.length; i++){
                       	content += '<div class="main-area-content">';
			content += '<span class="strong">' + res.replies[i].from + '</span>&nbsp;';
                       	content += 'on ' + new Date(res.replies[i].timestamp) + '&nbsp;';
			content += '<br /><br />';
		      	content +=  res.replies[i].text;
                       	content += '</div>';
                               
               }
		content += '</div>';
		content += '<div class="main-area-content">';	
		content += '<div class="comment"><textarea id="reply-text-input"></textarea><button type="button" id="btn-reply" style="margin-top:10px;">Reply</button></div>';
		content += '</div>'; 
		content += '</div>';
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
				};
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
		$("#btn-follow").hide();
		$("#btn-unfollow").hide();
		if(res.f_list && res.f_list.indexOf(res.requester_email) != -1){
			$("#btn-unfollow").show();
		}else{
			$("#btn-follow").show();
		}  		
        
	}
	
	function add_new_members(res) {
		
		$("#new-group-area").html('');
		
        var content = '<div class="comment">';
        
        content += '<h3>Add New Members</h3><hr /><br />';
        content += '<form id="new-members-form">';
		content += '<span class="strong">Emails Separated by Commas : </span> <br />';
        content += '<input id="new-member-emails" type="text" style="width: 100%; box-sizing: border-box;"></input> <br /> <br />';
		
		content += '<button type="button" id="btn-add-members" style="margin-top:10px;">Add Members</button>';

		content += '</form></div>';
        
        $("#new-group-area").html(content);
        
		params = {'group_name': res.group_name};

		var member_add = bind(add_members, params);
		$("#btn-add-members").unbind("click");
        $("#btn-add-members").bind("click");
		$("#btn-add-members").click(member_add);

		$('#group-display-area').hide();
		
		$("#new-group-area").show();
	}
	
	function new_post(res){
		
		var active_group = $("#active_group").text();
        var content = '<div class="main-area-content">';
        content += '<div class="comment">';
		content += '<span class="strong">To : </span>';
		content += '<span id="new-post-to">' + active_group + '</span> <br />';
		content += '<span class="strong">Subject : </span> <br />';
                content += '<input id="new-post-subject" type="text" style="width: 100%; box-sizing: border-box;"></input> <br /> <br />';
		content += '<textarea id="new-post-text" style="height:150px;"></textarea>';
		content += '<button type="button" id="btn-post" style="margin-top:10px;">Post</button>';
		content += '</div>';

        content += '</div>';
        $("#main-area").html(content);

		params = {'requester_email':res.user};
		var ins_post = bind(insert_post, params);
		$("#btn-post").unbind("click");
                $("#btn-post").bind("click");
		$("#btn-post").click(ins_post);
		$('.row-item').css("background-color","white");
	}
	
	
	function new_group(res){
		
		$("#new-group-area").html('');
		
        var content = '<div class="comment">';
        
        content += '<form id="new-group-form">';
		content += '<span class="strong">New Group Name : </span> <br />';
        content += '<input id="new-group-name" type="text" style="width: 100%; box-sizing: border-box;"></input> <br /> <br />';
		
		content += '<span class="strong">New Group Privacy Settings : </span> <br />';
		content += '<input type="radio" name="pubpriv" value="public" id="rdo-pub-create-group"> Public<br />';
		content += 'All users will be able to view and search for this group by name.<br />';
		
		content += '<input type="radio" name="pubpriv" value="private" id="rdo-priv-create-group"> Private<br />';
		content += 'Only users added to this group by admins will be notified about the group.<br /><br />';
		
		content += '<button type="button" id="btn-new-create-group" style="margin-top:10px;">Create</button>';
		
		
		content += '</form></div>';
        
        $("#new-group-area").html(content);
        
        params = {'requester_email':res.user};

		var cr_group = bind(create_group, params);
		$("#btn-new-create-group").unbind("click");
        $("#btn-new-create-group").bind("click");
		$("#btn-new-create-group").click(cr_group);

		$('#group-display-area').hide();
		
		$("#new-group-area").show();
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
		return {'date':dateStr, 'time': timeStr};
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
        var active_group = $("#active_group").text();
		list_posts({'load':false, 'active_group': active_group});
	}
	

	
	/* Handle based on URLs */
	
	if (window.location.pathname.indexOf('/groups') != -1) {
		list_groups();
		var groups_table = $("#groups-table");
		groups_table.children().first().click();
	} else if (window.location.pathname.indexOf('/posts') != -1) {
		init_posts_page();	
		setInterval(refresh_posts, 10000);
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
