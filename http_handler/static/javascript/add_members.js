$(document).ready(function() {

    var website = $("#website-name").text();
    var group_name = $.trim($("#group-name").text());

    var btn_add_members = $("#btn-add-members");

    btn_add_members.click(function() {
        var params = {
            'group_name': group_name,
            'emails': $('#new-member-emails').val(),
        };
        params.add_as_mods = (website == "squadbox");

        $.post('/add_members', params,
            function(res) {
                if (res.status) $('#new-member-emails').val("");
                notify(res, true);
            }
        );
    });

    $(".default-text").blur();
    tinyMCE.init({
        mode: "textareas",
        theme: "advanced",
        theme_advanced_buttons1: "bold,italic,underline,strikethrough,|,justifyleft,justifycenter,justifyright,justifyfull,|,blockquote",
        theme_advanced_toolbar_location: "top",
        theme_advanced_toolbar_align: "left",
        theme_advanced_statusbar_location: "bottom",
        theme_advanced_resizing: true
    });

});