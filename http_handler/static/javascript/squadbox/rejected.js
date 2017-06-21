$(document).ready(function() {

	var delete_btn = $('#delete-btn'),
		group_name = $('#group-name')[0].innerHTML;

	delete_btn.click(function(){
		if (confirm("Are you sure you want to delete the selected messages? This cannot be undone.")) {
			var to_delete = [];
			$("input:checkbox:checked").each(function(){
				var val_str = $(this).val();
				var [_, thread_id, post_id] = val_str.split('-');
				to_delete.push(thread_id + '-' + post_id);
			});

			$.post('/delete_posts', {'id_pairs' : to_delete.join(',')}, 
				function(res) {
					if (res.status) window.location.href = "/groups/" + group_name + "/rejected";
					notify(res, true);
			});

		}
	})
});