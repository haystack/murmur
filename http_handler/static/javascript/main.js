String.prototype.trunc = String.prototype.trunc ||
      function(n){
          return this.length>n ? this.substr(0,n-1)+'&hellip;' : this;
      };

$(document).ready(function(){
	/* Global Objects */

	posts_local_data = {};

	groups_local_data = {};
	
	posts_list = [];
 
	window.onpopstate = function(event) {
		if (window.location.pathname.indexOf('/posts') != -1) {
			if (event.state.thread_id) {
				$("#main-area").html(event.state.code);
				posts_local_data.selected_thread = event.state.thread_id;
				$('.row-item').css("background-color","white");
				$('#' + event.state.thread_id).css("background-color","lightyellow");
			} else {
				$('.row-item').css("background-color","white");
				$("#main-area").html(event.state.code);
			}
		} else {	
			$("#group-info").html(event.state.code);
			groups_local_data.selected_group = event.state.group_name;
			$('.row-item').css("background-color","white");
			$('#' + event.state.group_name).css("background-color","lightyellow");
		}
	};
 

	/* Dynamic Table Definitions */	
	
	members_table = $('#members-table').dataTable();

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
				url: 'list_my_groups', 
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

	subscribe_group = 
		function(params){
			$.post('subscribe_group', params, 
				function(res){
					if (res.status) {
						$('#list-group-names').prepend('<li><a href="/posts?group_name=' + params.group_name + '">' + params.group_name + '</a></li>');
						list_groups(params);
						group_info(params);
					}
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
					params.thread_id = parseInt(getUrlParameter('tid'));
					if (params.thread_id > -1) {
						params.load = true;
					}
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
                		$('#' + params.thread_id + ' > div:nth-child(2)').after('<div><span class="label2 following" style="background-color: #3D7AA6;">Following</span></div>');
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
                       $('#' + params.thread_id).children()[2].remove();
                    }
					notify(res, true);
				}
			);	
		};
		
		
	
	mute_thread = 
		function(params){
			$.post('mute_thread', {'requester_email': params.requester_email, 
						  'thread_id': params.thread_id,
						  'msg_id': params.msg_id
					  	}, 
				function(res){
					if(res.status){
						$("#btn-mute").hide();
                		$("#btn-unmute").show();
                		$('#' + params.thread_id + ' > div:nth-child(2)').after('<div><span class="label2 following" style="background-color: #3D7AA6;">Muted</span></div>');
					}
					notify(res, true);
				}
			);	
		};
	
	unmute_thread = 
		function(params){
			$.post('unmute_thread', {'requester_email': params.requester_email, 
						  'thread_id': params.thread_id,
						  'msg_id' : params.msg_id
					  	}, 
				function(res){
					if(res.status){
                       $("#btn-mute").show();
                       $("#btn-unmute").hide();
                       $('#' + params.thread_id).children()[2].remove();
                    }
					notify(res, true);
				}
			);	
		};
		
	insert_post = 
		function(params){
			params.msg_text = CKEDITOR.instances['new-post-text'].getData();
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
			params.msg_text = CKEDITOR.instances['reply-text-input'].getData();
			if(params.subject.substr(0,3).toLowerCase() == 're:'){
				params.subject = params.subject.substr(3,len(params.subject)).trim();
			}
			params.poster_email = params.requester_email;
			delete params.text;
			posts_local_data.selected_thread = params.thread_id;
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
			if (res.groups.length == 0) {
				var content = '<div class="add-padding"><i>You are not in any groups yet. <a href="/group_list">Join or create a new group.</a></i></div>';
				$("#groups-table").append(content);
			}
			
			var group_list = [];
			
			for(var i = 0; i< res.groups.length; i++){
				
				var group_in = {"name": res.groups[i].name,
								  "desc": res.groups[i].desc
								 };
				group_list.push(group_in);
				
				var content = '<li class="row-item" id="'+ res.groups[i].name+'">';
				content += '<span class="strong">' + res.groups[i].name + '</span>';
				if (res.groups[i].member == true)
					content += '<span class="member label">Member</span>';
				
				if (res.groups[i].admin == true)
					content += '<span class="admin label">Admin</span>';
				
				if (res.groups[i].mod == true)
					content += '<span class="mod label">Mod</span>';
				
				content += '<br /><span class="italic-med">' + res.groups[i].desc + '</span>';
				
				content += '</li>';
				var curr_row = $(content);
				groups_table.append(curr_row);
								 
				var params = {'requester_email': res.user, 
						'group_name': res.groups[i].name
					};
				var f = bind(group_info, params);
				
				curr_row.on('click',f);
			}
			
			var groups = new Bloodhound({
				datumTokenizer: Bloodhound.tokenizers.obj.whitespace("name", "desc"),
				queryTokenizer: Bloodhound.tokenizers.whitespace,
				local: group_list
			});
			groups.initialize();
			
			$("#text-search-group").typeahead({
				minLength: 2,
				highlight: true,
				hint: false,
			}, {
				name: 'groups',
				displayKey: 'name',
				source: groups.ttAdapter(),
				highlighter: function(item) {
	                return item.name + item.desc;
	            },
	            templates: {
				    empty: [
				      '<div class="empty-message">',
				      'Unable to find any groups that match the current query',
				      '</div>'
				    ].join('\n'),
				    suggestion: function (group) {
	            		return '<a href="/groups/'+ group.name + '"><div class="suggestion">' + group.name + '<br /><span class="italic-med">' + group.desc.trunc(40) + '</span></div></a>';
	        		}
			  	}
	            
			}).on('typeahead:selected', function($e, datum) {
				window.location.href = "/groups/" + datum.name;
			});
		}
	}
	
	function populate_members_table(res){
		members_table.fnClearTable();
		for(var i = 0; i< res.members.length; i++){
			tableData = [];
			email = res.members[i].email;
			tableData.push(email);
			admin = res.members[i].admin;
			moderator = res.members[i].moderator;
			if (admin == true) {
				tableData.push('<span class="glyphicon glyphicon-ok" aria-hidden="true"></span>');					;
			}
			else {
				tableData.push(" ");
			}
			if (moderator == true) {
				tableData.push('<span class="glyphicon glyphicon-ok" aria-hidden="true"></span>');					;
			}
			else {
				tableData.push(" ");
			}
			curr = members_table.fnAddData(tableData);
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
		
		info += "This group is <span class='strong'>";
		if (res.public) {
			info += "Public";
		} else {
			info += "Private";
		}
		info += "</span>.<br />";
		
		if (!res.allow_attachments) {
			info += '<span class="strong">No Attachments</span> are allowed.';
		} else {
			info += 'Attachments <span class="strong">are allowed</span>.';
		}
		
		info += '<br /> <br />';
		info += '<a href="/posts?group_name=' + res.group_name + '"><button type="button">View Posts</button></a> <br /> <br />';
		$("#group-info").html(info);
		
		if (getUrlParameter('group_name') == undefined) {
			history.replaceState({'code': info, 'group_name': res.group_name}, res.group_name, "my_groups?group_name=" + res.group_name);
		} else {
			history.pushState({'code': info, 'group_name': res.group_name}, res.group_name, "my_groups?group_name=" + res.group_name);
		}
		
   
		$('#group-display-area').show();
		var params = {'requester_email': res.user, 
					  'group_name': res.group_name,
					  'curr_row': curr_row
					};
		$("#btn-edit-group-info").unbind("click");
		$("#btn-edit-settings").unbind("click");
 		$("#btn-activate-group").unbind("click");
 		$("#btn-deactivate-group").unbind("click");
 		$("#btn-subscribe-group").unbind("click");
 		$("#btn-unsubscribe-group").unbind("click");
 		$("#btn-add-members").unbind("click");
 		
 		$("#btn-edit-group-info").bind("click");
 		$("#btn-edit-settings").bind("click");
 		$("#btn-activate-group").bind("click");
 		$("#btn-deactivate-group").bind("click");
 		$("#btn-subscribe-group").bind("click");
 		$("#btn-unsubscribe-group").bind("click");
 		$("#btn-add-members").bind("click");
 		
		var act_group = bind(activate_group, params);
		var deact_group = bind(deactivate_group, params);
		var sub_group = bind(subscribe_group, params);
		var unsub_group = bind(unsubscribe_group, params);
		
		$("#btn-edit-settings").click(function() {
			window.location.href = "/groups/" + res.group_name + "/edit_my_settings";
		});
		
		$("#btn-edit-group-info").click(function() {
			window.location.href = "/groups/" + res.group_name + "/edit_group_info";
		});

		$("#btn-activate-group").click(act_group);
		$("#btn-deactivate-group").click(deact_group);
		$("#btn-subscribe-group").click(sub_group);
		$("#btn-unsubscribe-group").click(unsub_group);
		$("#btn-add-members").click(function() {
			window.location.href = "/groups/" + res.group_name + "/add_members";
		});
		
		$("#btn-subscribe-group").hide();
		$("#btn-unsubscribe-group").hide();
		$("#btn-activate-group").hide();
		$("#btn-deactivate-group").hide();
		$("#btn-add-members").hide();
		$("#btn-edit-group-info").hide();

		$("#btn-edit-settings").show();
		if(res.admin){
			if(res.active){
				$("#btn-deactivate-group").show();
				
			} else{
				$("#btn-activate-group").show();
			}
			$("#btn-add-members").show();
			$("#btn-edit-group-info").show();
		}
		if(res.active){
			if(res.subscribed){
                    $("#btn-unsubscribe-group").show();
            } else{
                    $("#btn-subscribe-group").show();
            }
	
		}

	}
	
	function display_posts_list(thread_list, load_params, reset, user, member_group) {
		var posts_table = $("#posts-table"); 
		if(reset == true){
			posts_table.empty();
		}
		var selected_thread = posts_local_data.selected_thread;
		timestamp = new Date(0);
		
		for (var i = 0; i< thread_list.length; i++){
			d = format_date(new Date(thread_list[i].timestamp));
			var content = '<div class="left-column-area-metadata">';
			content += '<span class="gray">' + d.date + '</span><BR>';
			content += '<span class="gray">' + d.time + '</span><BR>';
			content += '<span class="unread">' + thread_list[i].replies.length + '</span> <br />';
			content += '</div>';
			content += '<div class= "left-column-area-content">';
			
			subj = thread_list[i].post.subject;
			if (subj.length > 90) {
				content +=  '<span class="strong">' + thread_list[i].post.subject.substring(0,90) + '...</span>';
			} else {
				content +=  '<span class="strong">' + thread_list[i].post.subject + '</span>';
			}
			content += '<span class="strong-gray ellipsis">' + thread_list[i].post.from + '</span>';
			content += '<span class="blurb ellipsis">' + strip(thread_list[i].post.text) + '</span>';
			content += '</div>';
			
			if (member_group.no_emails == true || member_group.always_follow_thread == false) {
				if (thread_list[i].following == true) {
					content += '<div><span class="label2 following" style="background-color: #3D7AA6;">Following</span></div>';
				}
			} else {
				if (thread_list[i].muting == true) {
					content += '<div><span class="label2 following" style="background-color: #3D7AA6;">Muted</span></div>';
				}
			}
				
			if (thread_list[i].tags.length > 0) {
				content += '<div>';
				for (var j = 0; j < thread_list[i].tags.length; j++) {
					content += '<span class="label2" style="background-color: #' + thread_list[i].tags[j].color + ';">' + thread_list[i].tags[j].name + '</span> ';
				}
				content += '</div>';
			}
			var curr_row = $('<li class="row-item" id="' + thread_list[i].thread_id + '">' + content + '</li>');
			var params = {'requester_email': user,
				'thread_id' : thread_list[i].thread_id, 
				 'post': thread_list[i].post,
				 'replies' : thread_list[i].replies,
				 'following' : thread_list[i].following,
				 'muting' : thread_list[i].muting,
				 'tags' : thread_list[i].tags,
				 'member_group': member_group,
			};
				
			var f = bind(load_post, params);
			if(thread_list[i].thread_id == load_params.thread_id){
				selected_thread = thread_list[i].thread_id;
			}
			if(new Date(thread_list[i].timestamp) > timestamp){
                                    timestamp = thread_list[i].timestamp;
                            }

			curr_row.on('click',f);
			
			if(reset){
				posts_table.append(curr_row);
			} else{
			 	var row = $('#' + thread_list[i].thread_id);
				if(row.length == 0){ 
					posts_table.prepend(curr_row);
				}else{
					posts_table.prepend(curr_row);
					row.remove();
					if(thread_list[i].thread_id == posts_local_data.selected_thread){
						curr_row.click();
					}
				}	
			}
		}
		posts_local_data.timestamp = timestamp;
		return selected_thread;
	}
	
	function populate_posts_table(res, load_params, reset){

		var selected_thread;
		if(res.status){
			posts_list = res.threads;
			selected_thread = display_posts_list(res.threads, load_params, reset, res.user, res.member_group);
			
			var p_list = [];
			
			for(var i = 0; i< res.threads.length; i++){
				post = {'subject': res.threads[i].post.subject,
						'text': strip(res.threads[i].post.text),
						'from': res.threads[i].post.from,
						'tid': res.threads[i].thread_id,
						'tags': res.threads[i].tags
						};
				p_list.push(post);
			}

		var posts = new Bloodhound({
			datumTokenizer: Bloodhound.tokenizers.obj.whitespace("text", "subject", "from"),
			queryTokenizer: Bloodhound.tokenizers.whitespace,
			local: p_list
		});
		posts.initialize();
		
		$("#text-search-post").typeahead({
			minLength: 2,
			highlight: true,
			hint: false,
		}, {
			name: 'posts',
			displayKey: 'subject',
			source: posts.ttAdapter(),
			highlighter: function(item) {
                return item.subject + item.text;
            },
              templates: {
			    empty: [
			      '<div class="empty-message">',
			      'unable to find any posts that match the current query',
			      '</div>'
			    ].join('\n'),
			    suggestion: function (post) {
            		return '<a href="/thread?group_name=' + res.group_name + '&tid=' + post.tid + '"><div class="suggestion">' + post.subject.trunc(43) + '<br />' + post.from + '<br />' + post.text.trunc(40) + '</div></a>';
        }
		  }
            
		}).on('typeahead:selected', function($e, datum) {
				window.location.href = '/thread?group_name=' + res.group_name + '&tid=' + datum.tid;
			});;
		
		}
		var posts_table = $("#posts-table"); 
		
		if(load_params.load == true){
			posts_table.find('#'+selected_thread).click();
			console.debug("load = true");
		}
	}
	
	
	function render_post(res){
	
		var content = '<div class="main-area-content">';
		content += '<div>';
		content += '<div style="float:right">';
		content += '<button type="button" id="btn-follow" style="margin:5px;">Follow</button>';
		content += '<button type="button" id="btn-unfollow" style="margin:5px;">Unfollow</button>';
		content += '<button type="button" id="btn-mute" style="margin:5px;">Mute</button>';
		content += '<button type="button" id="btn-unmute" style="margin:5px;">Unmute</button>';
		content += '</div>';
		content += '<div>';
		content += '<span class="postheader">' + res.post.subject + '</span>';
		if (res.tags.length > 0) {
			for (var j = 0; j < res.tags.length; j++) {
				content += '<span class="label2" style="position: relative; top: -3px; background-color: #' + res.tags[j].color + ';">' + res.tags[j].name + '</span> ';
			}
		}
		content += '<br>';
		content += '<span class="strong">From: </span> <span class="strong-gray">' + res.post.from + '</span><br />';
		content += '<span class="strong">To: </span><span class="strong-gray">' + res.post.to + '</span> <br />';
		content += '<span class="strong">Date: </span><span class="strong-gray">' + new Date(res.post.timestamp) + '</span>';
		content += '</div>';
		content += '</div>';
		content += '<hr />';
		content += res.post.text;
		content += '<br />';
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
		content += '<textarea id="reply-text-input"></textarea>';
		content += "<script>CKEDITOR.replace( 'reply-text-input' );</script>";
		content += '<button type="button" id="btn-reply" style="margin-top:10px;">Reply</button></div>';
		content += '</div>';
		$("#main-area").empty();
        $("#main-area").html(content);
        
        history.pushState({'code': content, 'thread_id': res.thread_id}, res.post.subject, "posts?group_name=" + $("#active_group").text() + "&tid=" + res.thread_id);
		
        
        var gmail_quotes = $(".gmail_quote");
        var check = "---------- Forwarded message ----------";
        
        gmail_quotes.each(function () {
        	var text = $(this).text();
        	
        	if (text.substring(0, check.length) !== check) {
        		$(this).wrap( "<div class='accordian'></div>" );
        	}
        });
        
  //      var block = $( ".moz-cite-prefix" ).next();
  //      block.addClass("moz-blockquote");
  //      $(".moz-cite-prefix, .moz-blockquote").wrapAll( "<div class='accordian'><div></div></div>" );
        
        $(".accordian").prepend("<h3>...</h3>");
        
    	$(".accordian").accordion({collapsible: true, 
    							   active: false,
    							   heightStyle: "content"});
        
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
		$("#btn-mute").unbind("click");
		$("#btn-unmute").unbind("click");
		$("#btn-reply").bind("click");
		$("#btn-follow").bind("click");
		$("#btn-unfollow").bind("click");
		$("#btn-unfollow").bind("click");
		$("#btn-mute").bind("click");
		var ins_reply = bind(insert_reply, params);
		var flw_thread = bind(follow_thread, params);
		var unflw_thread = bind(unfollow_thread, params);
		var m_thread = bind(mute_thread, params);
		var um_thread = bind(unmute_thread, params);
		$("#btn-reply").click(ins_reply);
		$("#btn-follow").click(flw_thread);
		$("#btn-unfollow").click(unflw_thread);
		$("#btn-mute").click(m_thread);
		$("#btn-unmute").click(um_thread);
		$("#btn-follow").hide();
		$("#btn-unfollow").hide();
		$("#btn-mute").hide();
		$("#btn-unmute").hide();
		if (res.member_group.no_emails == true || res.member_group.always_follow_thread == false) {
			if (res.following){
				$("#btn-unfollow").show();
			} else{
				$("#btn-follow").show();
			} 
		} else {
			if (res.muting){
				$("#btn-unmute").show();
			} else{
				$("#btn-mute").show();
			}
		} 		
        
	}
	
	var getUrlParameter = function getUrlParameter(sParam) {
	    var sPageURL = decodeURIComponent(window.location.search.substring(1)),
	        sURLVariables = sPageURL.split('&'),
	        sParameterName,
	        i;
	
	    for (i = 0; i < sURLVariables.length; i++) {
	        sParameterName = sURLVariables[i].split('=');
	
	        if (sParameterName[0] === sParam) {
	            return sParameterName[1] === undefined ? true : sParameterName[1];
	        }
	    }
	};
	
	
	function new_post(res){
		
		var active_group = $("#active_group").text();
        var content = '<div class="main-area-content">';
        content += '<div class="comment">';
		content += '<span class="strong">To : </span>';
		content += '<span id="new-post-to">' + active_group + '</span> <br />';
		content += '<span class="strong">Subject : </span> <br />';
                content += '<input id="new-post-subject" type="text" style="width: 100%; box-sizing: border-box;"></input> <br /> <br />';
		content += '<textarea id="new-post-text" style="height:150px;"></textarea>';
		
		content += "<script>CKEDITOR.replace( 'new-post-text' );</script>";
		
		content += '<button type="button" id="btn-post" style="margin-top:10px;">Post</button>';
		content += '</div>';

        content += '</div>';
        $("#main-area").html(content);
        
        history.pushState({'code': content}, "New Post", "posts?group_name=" + $("#active_group").text() + '#new_post');
		

		params = {'requester_email':res.user};
		var ins_post = bind(insert_post, params);
		$("#btn-post").unbind("click");
                $("#btn-post").bind("click");
		$("#btn-post").click(ins_post);
		$('.row-item').css("background-color","white");
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
	 	history.replaceState({'code': $("#main-area").html()}, '');
	 	
		$.post('list_my_groups', {},
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
	
	if (window.location.pathname.indexOf('/my_groups') != -1) {
		list_groups();
		var groups_table = $("#groups-table");
		group_name = getUrlParameter('group_name');
		if (group_name != undefined) {
			$("#" + group_name).click();
		} else {
			groups_table.children().first().click();
		}
	} else if (window.location.pathname.indexOf('/posts') != -1) {
		init_posts_page();	
		setInterval(refresh_posts, 10000);
	}
	
	function strip(html){
   		return html.replace(/<(?:.|\n)*?>/gm, ' ');
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
