$(document).ready(function() {

    var btn_create_group = $("#btn-new-create-group");
    var website = $("#website-name").text();

    btn_create_group.click(function() {

        var params = {
            'group_name' : $("#group-name").val(),
            'group_desc' : $("#group-description").val(),
            'send_rejected_tagged' : true,
            'store_rejected' : true,
            'mod_rules' : null,
            'mod_edit_wl_bl' : true,
            'auto_approve' : false,
            'attach' : $('input[name=attach]:checked', '#group-form').val(),
        };

        if (website == "squadbox") { // all squads private 
            params.public = false;
            params.send_rejected_tagged = $('#send-rejected')[0].checked;
            params.store_rejected = $('#store-rejected')[0].checked;
            params.mod_rules = $('#edit-mod-rules').val();
            params.mod_edit_wl_bl = $('#mod-edit-wl-bl')[0].checked;
            params.auto_approve = $('#auto-approve')[0].checked;
        } else if (website == "murmur") {
            params.public = $('input[name=pubpriv]:checked', '#group-form').val();

        }


        $.post('create_group', params,
            function(res) {
                notify(res, true);
                if (res.status) {
                    window.location = '/groups/' + params.group_name;
                }
            }
        );
    });
});