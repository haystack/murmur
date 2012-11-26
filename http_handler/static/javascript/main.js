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
			{"bSortable": false, "sWidth": "50%"}
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
					populate_members_table(res, params.curr_row);
				}
			);	
		}
	

	subscribe_group = 
		function(params){
			$.post('subscribe_group', params, 
				function(res){
					notify(res);
				}
			);	
		}
		
		
	unsubscribe_group = 
		function(params){
			$.post('unsubscribe_group', params, 
				function(res){
					notify(res);
				}
			);	
		}

	activate_group = 
		function(params){
			$.post('activate_group', params, 
				function(res){
					notify(res);
				}
			);	
		}
		
	
	deactivate_group = 
		function(params){
			$.post('deactivate_group', params, 
				function(res){
					notify(res);
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
		console.log(res)
		if(res.status){
			for(var i = 0; i< res.groups.length; i++){
				curr = groups_table.fnAddData( [
									res.groups[i].name
								  ]);
				var params = {'requester_email': 'anantb@csail.mit.edu', 
							  'group_name': res.groups[i].name,
							  'curr_row': curr
							 }
				var f = bind(group_info, params)
				curr_row = groups_table.fnGetNodes(curr);
				$(curr_row).click(f);
			}
		}
	}
	
	function populate_members_table(res, curr_row){
		members_table.fnClearTable();
		for(var i = 0; i< res.members.length; i++){
			curr = members_table.fnAddData( [
								res.members[i].email,
								res.members[i].active
							  ]);
		}
		if(curr_row !== undefined){
			$('td', groups_table.fnGetNodes()).css("background-color","white");
			$('td', groups_table.fnGetNodes(curr_row)).css("background-color","lightyellow");
		}	
	}

	list_groups();
});

				
	




