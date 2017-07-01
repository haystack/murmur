$(document).ready(function() {

    var group_name = $.trim($("#group-name").text()),
        btn_add_blacklist = $("#btn-add-blacklist");


    btn_add_blacklist.click(function() {
        var params = {
            'group_name': group_name,
            'senders': $('#new-blacklist-emails').val(),
        };

        $.post('/blacklist', params,
            function(res) {
                if (res.status) $('#new-blacklist-emails').val("");
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