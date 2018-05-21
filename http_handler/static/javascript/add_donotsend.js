$(document).ready(function() {

    var group_name = $.trim($("#group-name").text()),
        btn_add_dissimulate = $("#btn-add-dissimulate");


        btn_add_dissimulate.click(function() {
        var params = {
            'group_name': group_name,
            'senders': $('#new-dissimulate-emails').val(),
        };

        $.post('/donotsend_list', params,
            function(res) {
                $('#donotsend-msg').hide();
                if (res.status) {
                    $('#new-dissimulate-emails').val("");
                    if (res.code) { 
                        // some emails are not added since they are not members of the group
                        $('#donotsend-msg').show();
                        $('#donotsend-msg').text(res['code']);
                    }
                    else {                        
                        notify(res, true);
                    }
                }
                else {
                    notify(res, false);
                }
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