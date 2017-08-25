$(document).ready(function() {

    var website = $("#website-name").text(),
        old_group_name = $.trim($("#orig-group-name").text()),
        btn_cancel_settings = $("#btn-cancel-settings"),
        btn_save_settings = $("#btn-save-settings");

    btn_cancel_settings.click(function() {
        window.location = '/groups/' + old_group_name;
    });

    btn_save_settings.click(function() {
        var params = {
            'old_group_name': old_group_name,
            'new_group_name': $("#group-name").val(),
            'group_desc': $("#group-description").val(),
            'attach': $('input[name=attach]:checked', "#group-form").val(),
        }

        if (website == "squadbox") { // all squads private 
            params.public = false;
            params.send_rejected_tagged = $('#send-rejected')[0].checked;
            params.store_rejected = $('#store-rejected')[0].checked;
            params.mod_edit = $('#mod-edit-wl-bl')[0].checked;
            params.mod_rules = $("#edit-mod-rules").val();
            params.auto_approve = $('#auto-approve')[0].checked;
            
        } else if (website == "murmur") {
            params.public = $('input[name=pubpriv]:checked', '#group-form').val();

            // just go with the defaults for these for now
            params.send_rejected_tagged = true;
            params.store_rejected = true;
            params.mod_edit = true;
            params.mod_rules = null;
            params.auto_approve = false;
        }

        $.post('/edit_group_info', params,
            function(res) {
                if (res.status) {
                    notify(res, true);
                    setTimeout(function() {
                        if (params.new_group_name.length > 0) {
                            window.location = "/groups/" + params.new_group_name + '/edit_group_info';
                        } else {
                            window.location = "/groups/" + params.old_group_name + '/edit_group_info';
                        }
                    }, 1000);
                }
            }
        );
    });

});