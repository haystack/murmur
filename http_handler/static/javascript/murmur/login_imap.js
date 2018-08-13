$(document).ready(function() {
    
    var user_name = $.trim($('#user_email').text()),
        btn_login = $("#btn-login");
    
    
        btn_login.click(function() {
                var params = {
                    'email': $("#input-email").val(),
                    'host': $("#input-host").val(),
                    'password': $("#input-password").val()
                };
        
                $.post('/login_imap', params,
                    function(res) {
                        // $('#donotsend-msg').hide();
                        console.log(res);
                        if (res.status) {
                            // $('#new-dissimulate-emails').val("");
                            if (res.code) { 
                                // some emails are not added since they are not members of the group
                                // $('#donotsend-msg').show();
                                // $('#donotsend-msg').html(res['code']);
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

        $("#input-email").keyup(function( event ) {
            guess_host( $(this).val() );
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

    function guess_host( email_addr ) {
        if( email_addr.includes("gmail")) $("#input-host").val("imap.gmail.com");
        else if ( email_addr.includes("yahoo")) $("#input-host").val("imap.mail.yahoo.com");
        else if ( email_addr.includes("csail")) $("#input-host").val("imap.csail.mit.edu");
        else if ( email_addr.includes("mit")) $("#input-host").val("imap.exchange.mit.edu");
    }
});