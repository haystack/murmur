$(document).ready(function() {
    
    var user_name = $.trim($('#user_email').text()),
        btn_login = $("#btn-login"),
        btn_code_sumbit = $("#btn-code-submit");
    

    // Create the sandbox:
    // window.sandbox = new Sandbox.View({
    //     el : $('#sandbox'),
    //     model : new Sandbox.Model()
    //   });

    // init editor 
    var editor = CodeMirror.fromTextArea(document.getElementById("code"), {
        mode: {name: "python",
            version: 3,
            singleLineStringErrors: false},
        lineNumbers: true,
        indentUnit: 4,
        matchBrackets: true
    });

    toggle_login_mode();
	
	$('input[type=radio][name=auth-mode]').change(function() {
        toggle_login_mode();      
    });
	
	function toggle_login_mode() {
		oauth = $('#rdo-oauth').is(":checked");
		if (oauth) {
            $(".oauth").show();
            $(".plain").hide();
		} else {
			$(".oauth").hide();
            $(".plain").show();
		}
	}

    
        btn_login.click(function() {
                var params = {
                    'email': $("#input-email").val(),
                    'host': $("#input-host").val(),
                    'password': $('#rdo-oauth').is(":checked") ? $("#input-access-code").val() : $("#input-password").val(),
                    'is_oauth': $('#rdo-oauth').is(":checked")
                };
        
                $.post('/login_imap', params,
                    function(res) {
                        // $('#donotsend-msg').hide();
                        console.log(res);
                        
                        // Auth success
                        if (res.status) {
                            // Show coding interfaces 
                            $("#login-email-form").hide();
                            if ('imap_code' in res) 
                                editor.setValue( res['imap_code'] );
                            
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

        btn_code_sumbit.click(function() {
            var params = {
                'email': $("#input-email").val(),
                'code': editor.getValue()
            };
    
            $.post('/run_mailbot', params,
                function(res) {
                    // $('#donotsend-msg').hide();
                    console.log(res);
                    
                    // Auth success
                    if (res.status) {
                        // TODO spin cogs, give feedback it's running

                        var currentdate = new Date();
                        var datetime = (currentdate.getMonth()+1) + "/"
                        + currentdate.getDate() + "/" 
                        + currentdate.getFullYear() + " @ "  
                        + currentdate.getHours() + ":"  
                        + currentdate.getMinutes() + ":" 
                        + currentdate.getSeconds()
                        + " | ";

                        if(res['imap_error'])  {
                            $( "<p>" + datetime + res['imap_log'] + "</p>" ).appendTo( "#console" )
                              .addClass("error");
                        }
                        else {
                            $( "<p>" + datetime + res['imap_log'] + "</p>" ).appendTo( "#console" )
                              .addClass("info");
                        }

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

    function guess_host( email_addr ) {
        $("#link-less-secure").attr('href', "");
        $("#rdo-oauth").attr('disabled', "");
        
        if( email_addr.includes("gmail")) {
            $("#input-host").val("imap.gmail.com");
            $("#link-less-secure").attr('href', "https://myaccount.google.com/lesssecureapps");
            $("#rdo-oauth").removeAttr('disabled');
        }
        else if ( email_addr.includes("yahoo")) $("#input-host").val("imap.mail.yahoo.com");
        else if ( email_addr.includes("csail")) $("#input-host").val("imap.csail.mit.edu");
        else if ( email_addr.includes("mit")) $("#input-host").val("imap.exchange.mit.edu");
        else $("#input-host").val("");
    }
});