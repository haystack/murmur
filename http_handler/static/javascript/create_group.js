$(document).ready(function() {

    var btn_create_group = $("#btn-new-create-group");
    var website = $("#website-name").text();

    btn_create_group.click(function() {
        var params = {};
        params.group_name = $("#new-group-name").val();
        params.group_desc = $("#new-group-description").val();
        if (website == "squadbox") { // all squads private 
            params.public = false;
        } else if (website == "murmur") {
            params.public = $('input[name=pubpriv]:checked', '#new-group-form').val();
        }
        params.attach = $('input[name=attach]:checked', '#new-group-form').val();

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