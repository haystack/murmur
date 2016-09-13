// $(document).ready(function(){

// 	var user_name = $.trim($('#user_email').text());
// 	var group_name = $.trim($("#group-name").text());
	
// 	var member = $.trim($(".member").text()) == "Member";
// 	var admin = $.trim($(".admin").text()) == "Admin";
// 	var mod = $.trim($(".mod").text()) == "Mod";
// 	var group_active = $.trim($(".group_active").text()) == "True";
	
	
// 	if (admin) {
// 		var members_table = $('#members-table').dataTable({
// 			"aoColumns": [
// 				{ 'bSortable': false},
// 				null,
// 				null,
// 				null,
// 				null
// 			]
// 		});
// 		var lists_table = $('#lists-table').dataTable({
// 			"aoColumns": [
// 				{ 'bSortable': false},
// 				null,
// 				null,
// 				null,
// 				null
// 			]
// 		});
// 	} else {
// 		var members_table = $('#members-table').dataTable({}),
// 			lists_table = $('#lists-table').dataTable({});
// 	}
	
// 	var btn_edit_group_info = $("#btn-edit-group-info"),
// 		btn_edit_settings = $("#btn-edit-settings"),
// 		//btn_activate_group = $("#btn-activate-group"),
// 		//btn_deactivate_group = $("#btn-deactivate-group"),
// 		btn_add_members = $("#btn-add-members"),
// 		btn_subscribe_group = $("#btn-subscribe-group"),
// 		btn_unsubscribe_group = $("#btn-unsubscribe-group"),
// 		btn_delete_members = $("#btn-del-members"),
// 		btn_set_admin = $("#btn-set-admin"),
// 		btn_set_mod = $("#btn-set-mod"),
// 		btn_add_list = $('#btn-add-list');
		
// 	subscribe_group = 
// 		function(params){
// 			$.post('/subscribe_group', params, 
// 				function(res){
// 					if (res.status) {
// 						member = true;
// 						fix_visibility();
// 						$(".member").text('Member');
// 						$(".member").show();
// 						var row_info = members_table.fnAddData( [
// 					        user_name,
// 					        new Date().toLocaleString(),
// 					        admin,
// 					        mod,
// 					        ] );
// 						var row = members_table.fnSettings().aoData[ row_info[0] ].nTr;
// 						row.className = "my_row";
// 					}
// 					if (res.redirect) {
// 						window.location.href = res.url;
// 					}
// 					notify(res, true);
// 				}
// 			);	
// 		};
		
		
// 	unsubscribe_group = 
// 		function(params){
// 			$.post('/unsubscribe_group', params, 
// 				function(res){
// 					if (res.status) {
// 						member = false;
// 						fix_visibility();
// 						$(".member").hide();
// 						var aPos = members_table.fnGetPosition($(".my_row").get(0)); 
// 						members_table.fnDeleteRow(aPos);
// 					}
// 					notify(res, true);
// 				}
// 			);	
// 		};
		
// 	// activate_group = 
// 	// 	function(params){
// 	// 		$.post('/activate_group', params, 
// 	// 			function(res){
// 	// 				if (res.status) {
// 	// 					$(".group_active").text('True');
// 	// 					group_active = true;
// 	// 					fix_visibility();
// 	// 				}
// 	// 				notify(res, true);
// 	// 			}
// 	// 		);	
// 	// 	};
		
	
// 	// deactivate_group = 
// 	// 	function(params){
// 	// 		$.post('/deactivate_group', params, 
// 	// 			function(res){
// 	// 				if (res.status) {
// 	// 					$(".group_active").text('False');
// 	// 					group_active = false;
// 	// 					fix_visibility();
// 	// 				}
// 	// 				notify(res, true);
// 	// 			}
// 	// 		);	
// 	// 	};

// 	post_edit_members = 
// 		function(params) {
// 			$.post('/edit_members', params,
// 				function(res){
// 					notify(res,true);
// 					setTimeout(function(){
// 						window.location.reload();
// 					},400);
// 				}
// 			);
// 		};

// 	delete_list = 
// 		function(params){
// 			$.post('/delete_list', params, 
// 				function(res){
// 					if (res.status) {
// 						fix_visibility();
// 					}
// 					notify(res, true);
// 				}
// 			);
// 		};


// 	var toDelete = "";
// 	var toAdmin = "";
// 	var	toMod = "";

// 	edit_members_table_del = function(params) {
// 		$('.checkbox-user').each(function() {
// 		if (this.checked==true)
// 			toDelete= toDelete + (this.id) + ",";
// 		});
		
// 		names = "Are you sure you want to delete the selected users?";
// 		var c = confirm(names);
		
// 		if (c) {
// 			params.toAdmin = toAdmin;
// 			params.toMod = toMod;
// 			params.toDelete = toDelete;
// 			post_edit_members(params);
// 		}
// 	};
	
// 	edit_members_table_makeADMIN = function(params) {
// 		$('.checkbox-user').each(function() {
// 		if (this.checked==true)
// 			toAdmin= toAdmin + (this.id) + ",";
// 		});
// 		params.toAdmin = toAdmin;
// 		params.toMod = toMod;
// 		params.toDelete = toDelete;
// 		post_edit_members(params);
// 	};
			
// 	edit_members_table_makeMOD = function(params) {
// 		$('.checkbox-user').each(function() {
// 			if (this.checked == true)
// 				toMod = toMod + (this.id) + ",";
// 		});
// 		params.toAdmin = toAdmin;
// 		params.toMod = toMod;
// 		params.toDelete = toDelete;
// 		post_edit_members(params);
// 	};


// 	var actionSelect = $('#actionSelect');

// 	actionSelect.change(function(){

// 		var value = $(this).val();

// 		if (value == 'label') {
// 			return;
// 		}
// 		else if (value == 'addList'){
// 			window.location.href = window.location.href + '/add_list';
// 		}

// 		else if (value == 'deleteList'){
// 			var c = confirm("Are you sure you want to delete the selected lists?");
// 			if (c == true){
// 				edit_lists_delete();
// 			} else {
// 				$(this).val("label");
// 				return;
// 			}
// 		}
// 		else if (value == 'addPost'){
// 			edit_lists_make_canpost();
// 		}
// 		else if (value == 'addReceive'){
// 			edit_lists_make_canreceive();
// 		}
// 		else if (value =='removePost'){
// 			edit_lists_remove_canpost();
// 		}
// 		else if (value == 'removeReceive'){
// 			edit_lists_remove_canreceive();
// 		}
// 	});


// 	edit_lists_make_canpost = function() {
// 		$('.checkbox-list').each(function() {
// 			lists = [];
// 			if (this.checked) {
// 				lists.push(this.id);
// 			}
// 		});
// 		var params = {'group_name' : group_name, 'make_can_post' : lists};
// 		add_posting_lists(params);
// 	}

// 	edit_lists_make_canreceive = function() {
// 		$('.checkbox-list').each(function() {
// 			lists = [];
// 			if (this.checked) {
// 				lists.push(this.id);
// 			}
// 		});
// 		var params = {'group_name' : group_name, 'make_can_receive' : lists};
// 		add_receiving_lists(params);
// 	} 

// 	edit_lists_delete = function() {
// 		$('.checkbox-list').each(function() {
// 			lists = [];
// 			if (this.checked) {
// 				lists.push(this.id);
// 			}
// 		});

// 		var params = {'group_name' : group_name, 'to_delete' : lists};
// 		delete_lists(params);
// 	}

		
// 	bind_buttons();
// 	fix_visibility();
	
	
			
// 	function bind_buttons() {
// 		// btn_edit_group_info.unbind("click");
// 		// btn_edit_settings.unbind("click");
//  	// 	btn_activate_group.unbind("click");
//  	// 	btn_deactivate_group.unbind("click");
//  	// 	btn_subscribe_group.unbind("click");
//  	// 	btn_unsubscribe_group.unbind("click");
//  	// 	btn_add_members.unbind("click");
//  	// 	btn_delete_members.unbind("click");
//  	// 	btn_set_mod.unbind("click");
//  	// 	btn_set_admin.unbind("click");
//  	// 	btn_add_list.unbind("click");
 		
//  	// 	btn_edit_group_info.bind("click");
//  	// 	btn_edit_settings.bind("click");
//  	// 	btn_activate_group.bind("click");
//  	// 	btn_deactivate_group.bind("click");
//  	// 	btn_subscribe_group.bind("click");
//  	// 	btn_unsubscribe_group.bind("click");
//  	// 	btn_add_members.bind("click");
//  	// 	btn_delete_members.bind("click");
//  	// 	btn_set_mod.bind("click");
//  	// 	btn_set_admin.bind("click");
//  	//	btn_add_list.bind("click");
 		
// 		// var params = {'group_name': group_name};

//  	// 	var act_group = bind(activate_group, params);
// 		// var deact_group = bind(deactivate_group, params);
// 		// var sub_group = bind(subscribe_group, params);
// 		// var unsub_group = bind(unsubscribe_group, params);
// 		// var delete_members = bind(edit_members_table_del, params);
// 		// var make_admin = bind(edit_members_table_makeADMIN, params);
// 		// var make_mod = bind(edit_members_table_makeMOD, params);
// 		//var add_list = bind(add_list, params);
		
// 		btn_activate_group.click(act_group);
// 		btn_deactivate_group.click(deact_group);
// 		btn_subscribe_group.click(sub_group);
// 		btn_unsubscribe_group.click(unsub_group);
// 		btn_delete_members.click(delete_members);
// 		btn_set_mod.click(make_mod);
// 		btn_set_admin.click(make_admin);

// 		btn_add_members.click(function() {
// 			window.location = '/groups/' + group_name + '/add_members';
// 		});
		
// 		btn_edit_settings.click(function() {
// 			window.location = '/groups/' + group_name + '/edit_my_settings';
// 		});

// 		btn_edit_group_info.click(function() {
// 			window.location = '/groups/' + group_name + '/edit_group_info';
// 		});

// 		btn_add_list.click(function() {
// 			window.location ='/groups/' + group_name + '/add_list';
// 		});
// 	}
	
		
// 	function fix_visibility() {
// 		if (admin) {
// 			// if (group_active) {
// 			// 	btn_deactivate_group.show();
// 			// 	btn_activate_group.hide();
// 			// } else {
// 			// 	btn_deactivate_group.hide();
// 			// 	btn_activate_group.show();
// 			// }
// 			btn_add_members.show();
// 			btn_edit_group_info.show();
// 			btn_set_admin.show();
// 			btn_set_mod.show();
// 			btn_delete_members.show();
			
// 		} else {
// 			btn_add_members.hide();
// 			// btn_deactivate_group.hide();
// 			// btn_activate_group.hide();
// 			btn_set_mod.hide();
// 			btn_set_admin.hide();
// 			btn_delete_members.hide();
// 		}
		
// 		if (member) {
// 			btn_unsubscribe_group.show();
// 			btn_subscribe_group.hide();
// 		} else {
// 			btn_unsubscribe_group.hide();
// 			btn_subscribe_group.show();
// 		}
// 	}
// });


// // /* To avoid closure */	
// // function bind(fnc, val ) {
// // 	return function () {
// // 		return fnc(val);
// // 	};
// // }

// function notify(res, on_success){
// 	if(!res.status){
// 		noty({text: "Error: " + res.code, dismissQueue: true, timeout:2000, force: true, type: 'error', layout: 'topRight'});
// 	}else{
// 		if(on_success){
// 			noty({text: "Success!", dismissQueue: true, timeout:2000, force: true, type:'success', layout: 'topRight'});
// 		}
// 	}
// }
	
	
$(document).ready(function(){

	var user_name = $.trim($('#user_email').text()),
		group_name = $.trim($("#group-name").text()),
		member = $.trim($(".member").text()) == "Member",
		admin = $.trim($(".admin").text()) == "Admin",
		mod = $.trim($(".mod").text()) == "Mod",
		btn_edit_group_info = $("#btn-edit-group-info"),
		btn_edit_settings = $("#btn-edit-settings"),
		btn_add_members = $("#btn-add-members"),
		btn_subscribe_group = $("#btn-subscribe-group"),
		btn_unsubscribe_group = $("#btn-unsubscribe-group"),
		btn_delete_members = $("#btn-del-members"),
		btn_set_admin = $("#btn-set-admin"),
		btn_set_mod = $("#btn-set-mod"),
		btn_add_list = $('#btn-add-list'),
		action_select = $('#actionSelect');

	var admin_buttons = [btn_add_members, btn_edit_group_info, btn_set_admin, btn_set_mod, 
						btn_delete_members, btn_add_list, action_select];

	if (admin) {
		var members_table = $('#members-table').dataTable({
			"aoColumns": [ { 'bSortable': false}, null, null, null, null]
		}),
			lists_table = $('#lists-table').dataTable({
			"aoColumns": [ { 'bSortable': false}, null, null, null, null]
		});

	} else {
		var members_table = $('#members-table').dataTable({}),
			lists_table = $('#lists-table').dataTable({});
	}


	var post_edit_members = function(params) {
		$.post('/edit_members', params, function(res){
			notify(res,true);
			setTimeout(function(){
				window.location.reload();
			}, 400);
		});
	};

	var delete_list = function(params) {
		$.post('/delete_list', params, function(res){
			if (res.status) notify(res, true);
		});
	}

	var edit_lists_make_canpost = function() {
		var selected = get_selected('list'),
			params = {'group_name' : group_name, 'make_can_post' : selected};
		add_posting_lists(params);
	}

	var edit_lists_make_canreceive = function() {
		var selected = get_selected('list'),
			params = {'group_name' : group_name, 'make_can_receive' : selected};
		add_receiving_lists(params);
	} 

	var edit_lists_delete = function() {
		var selected = get_selected('list'),
			params = {'group_name' : group_name, 'to_delete' : selected};
		delete_lists(params);
	}

	// attach handlers to buttons 

	btn_add_members.click(function() {
		go_to('add_members');
	});
	
	btn_edit_settings.click(function() {
		go_to('edit_my_settings');
	});

	btn_edit_group_info.click(function() {
		go_to('edit_group_info');
	});

	btn_add_list.click(function() {
		go_to('add_list');
	});


	btn_subscribe_group.click(function(){

		var params = {'group_name' : group_name};

		$.post('/subscribe_group', params, function(res){
			if (res.status) {
				member = true;
				fix_visibility();
				$(".member").text('Member');
				$(".member").show();
				var row_info = members_table.fnAddData([user_name, new Date().toLocaleString(), admin, mod,]);
					row = members_table.fnSettings().aoData[ row_info[0] ].nTr;
				row.className = "my_row";
			}
			if (res.redirect) window.location.href = res.url;
			notify(res, true);
		});
	});

	btn_unsubscribe_group.click(function(){

		var params = {'group_name' : group_name};

		$.post('/unsubscribe_group', params, function(res){
			if (res.status) {
				member = false;
				fix_visibility();
				$(".member").hide();
				var aPos = members_table.fnGetPosition($(".my_row").get(0)); 
				members_table.fnDeleteRow(aPos);
			}
			notify(res, true);
		});
	});


	btn_delete_members.click(function(){

		var c = confirm("Are you sure you want to delete the selected users?");
		
		if (c) {
			var selected = get_selected('user'),
				params = {'group_name' : group_name, 
							'toAdmin' : [],
							'toMod' : [],
							'toDelete' : selected
						};

			post_edit_members(params);
		}
	});

	btn_set_mod.click(function(){

		var selected = get_selected('user'),
			params = {'group_name' : group_name, 
						'toAdmin' : [],
						'toMod' : selected,
						'toDelete' : []
					};

		post_edit_members(params);
	});

	btn_set_admin.click(function(){

		var selected = get_selected('user'),
			params = {'group_name' : group_name, 
						'toAdmin' : selected,
						'toMod' : [],
						'toDelete' : []
					};

		post_edit_members(params);
	});

	action_select.change(function(){

		var value = $(this).val();

		if (value == 'deleteList'){
			var c = confirm("Are you sure you want to delete the selected lists?");
			if (c) {
				edit_lists_delete();
			} else {
				$(this).val("label");
			}
		}
		else if (value == 'addPost'){
			edit_lists_make_canpost();
		}
		else if (value == 'addReceive'){
			edit_lists_make_canreceive();
		}
		else if (value =='removePost'){
			edit_lists_remove_canpost();
		}
		else if (value == 'removeReceive'){
			edit_lists_remove_canreceive();
		}
	});


	// etc
	function fix_visibility() {
		if (admin) {
			admin_buttons.forEach(function(b){
				b.show();
			});
		} else {
			admin_buttons.forEach(function(b){
				b.hide();
			});
		}		
		if (member) {
			btn_unsubscribe_group.show();
			btn_subscribe_group.hide();
		} else {
			btn_unsubscribe_group.hide();
			btn_subscribe_group.show();
		}
	}

	function get_selected(typeString) {

		var className = 'checkbox-' + typeString;
		var lists = [];
		$(className).each(function() {
			if (this.checked) lists.push(this.id);	
		});
		return lists;
	}

	function go_to(page) {
		window.location ='/groups/' + group_name + '/' + page;
	}

});

function notify(res, on_success){
	if (!res.status) {
		noty({text: "Error: " + res.code, dismissQueue: true, timeout:2000, force: true, type: 'error', layout: 'topRight'});
	} else {
		if (on_success) {
			noty({text: "Success!", dismissQueue: true, timeout:2000, force: true, type:'success', layout: 'topRight'});
		}
	}
}