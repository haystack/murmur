$(document).ready(function(){ 
	groups_table = $('#groups-table').dataTable({
		"sDom": '<"top"f<"clear">>rt<"bottom"ilp<"clear">>',
		"bPaginate": false,
		"bInfo": false,
		"bAutoWidth": false,
		"bFilter": false,
		"sWidth": "100%",
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
				}
			);	
		}

	subscribe_group = 
		function(params){
			$.post('subscribe_group', params, 
				function(res){
					group_info(params)
					//notify(res);
				}
			);	
		}
		
		
	unsubscribe_group = 
		function(params){
			$.post('unsubscribe_group', params, 
				function(res){
					group_info(params)
					//notify(res);
				}
			);	
		}

	activate_group = 
		function(params){
			$.post('activate_group', params, 
				function(res){
					group_info(params);
					//notify(res);
				}
			);	
		}
		
	
	deactivate_group = 
		function(params){
			$.post('deactivate_group', params, 
				function(res){
					group_info(params);
					//notify(res);
				}
			);	
		}				  


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
									res.groups[i].name
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
	}
	
	function populate_members_table(res){
		$('#main-area').show()
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
	
	function populate_group_info(res, curr_row){
		var info = "<h3>Group Info</h3><hr />";
		info += "Group Name: " + res.group_name + "<br />";
		info += "Active: " + res.active + "<br /> <br />";
		$("#group-info").html(info)
		var params = {'requester_email': res.user, 
					  'group_name': res.group_name,
					  'curr_row': curr_row
					 }
 		$("#btn-act-group").unbind("click");
 		$("#btn-deact-group").unbind("click");
 		$("#btn-sub-group").unbind("click");
 		$("#btn-unsub-group").bind("click");
 		$("#btn-act-group").bind("click");
 		$("#btn-deact-group").bind("click");
 		$("#btn-sub-group").bind("click");
 		$("#btn-unsub-group").unbind("click");
		var act_group = bind(activate_group, params);
		var deact_group = bind(deactivate_group, params);
		var sub_group = bind(subscribe_group, params);
		var unsub_group = bind(unsubscribe_group, params);
		$("#btn-act-group").click(act_group);
		$("#btn-deact-group").click(deact_group);
		$("#btn-sub-group").click(sub_group);
		$("#btn-unsub-group").click(unsub_group);
	}
	
	function highlight_table_row(table, curr_row){
		if(curr_row !== undefined){
			$('td', table.fnGetNodes()).css("background-color","white");
			$('td', table.fnGetNodes(curr_row)).css("background-color","lightyellow");
		}	
	}
	
	

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
    
	$(".default-text").blur();
	
	if(window.location.pathname.indexOf('/settings')!=-1){
		list_groups();
	}
});

				
	




