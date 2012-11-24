$(document).ready(function(){    
    dir_listing_table = $('#dir-listing-table').dataTable({
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
    
    
    msg_body_table = $('#msg-body-table').dataTable({
		"sDom": '<"top"f<"clear">>rt<"bottom"ilp<"clear">>',
        "bPaginate": false,
        "bInfo": false,
        "bAutoWidth": false,
        "bFilter": false,
        "sWidth": "100%",
        "aoColumns": [			
        	{"bSortable": false, "sWidth": "20%"},
        	{"bSortable": false, "sWidth": "60%"},
        	{"bSortable": false, "sWidth": "20%"}
        ]
    
    });
    
    get_dir_listing = function(params) {
		var jaqxhr = $.post("/ajax/dir_listing/",
			{},
			function(data){
				dir_listing_table.fnClearTable();
				populate_dir_listing_table(data);
			}); 			
			
	}
	
	
	get_msg_thread = function(id) {
		var jaqxhr = $.post("/ajax/msg_thread/",
			{'id':id},
			function(data){
				msg_thread_table.fnClearTable();
				populate_msg_thread_table(data);
			}); 
			
			
	}
	
	
	
	function bind(fnc, val ) {
		return function () {
			return fnc(val);
		};
	}
	
	function populate_dir_listing_table(data){
		var x = JSON.parse(data)
		console.log(x)
		for(var i = 0; i< x.projects.length; i++){
			curr = projects_table.fnAddData( [
								x.projects[i].title
							  ]);	
			var id = x.projects[i].id	
			var f = bind(get_tasks, id)		  
			curr_row = projects_table.fnGetNodes(curr);
			$(curr_row).click(f);
		}
		
	}
	
	
	function populate_msg_thread_table(data){
		var x = JSON.parse(data)
		for(var i = 0; i< x.tasks.length; i++){
		curr = tasks_table.fnAddData( [
       						x.tasks[i].desc,
       						x.tasks[i].owner_id,
       						x.tasks[i].step_deadline
		                  ]);					
		}	
	}
	
	

	get_dir_listing()
	
});




