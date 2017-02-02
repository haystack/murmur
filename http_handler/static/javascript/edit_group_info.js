$(document).ready(function() {

    var website = $("#website-name").text();

    var old_group_name = $.trim($("#group-name").text());

    var btn_cancel_settings = $("#btn-cancel-settings");

    btn_cancel_settings.click(function() {
        window.location = '/groups/' + old_group_name;
    });

    var btn_save_settings = $("#btn-save-settings");

    btn_save_settings.click(function() {
        var params = {
            'old_group_name': old_group_name,
            'new_group_name': $("#edit-group-name").val(),
            'group_desc': $("#edit-group-description").val(),
            'attach': $('input[name=attach]:checked', "#group-info-form").val(),
        }

        if (website == "squadbox") { // all squads private 
            params.public = false;
        } else if (website == "murmur") {
            params.public = $('input[name=pubpriv]:checked', '#group-info-form').val();
        }

        $.post('/edit_group_info', params,
            function(res) {
                if (res.status) {
                    notify(res, true);
                    setTimeout(function(){
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