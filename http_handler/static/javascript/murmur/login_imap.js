$(document).ready(function() {
    
    var user_name = $.trim($('#user_email').text()),
        btn_login = $("#btn-login"),
        btn_test_run = $("#btn-test-run"),
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

    var log_backup = "";

    // $("#password-container").hide();
    guess_host($("#user-full-email").text());
    toggle_login_mode();

    if(is_imap_authenticated) {
        fetch_log(); 
    }

    if(is_running) {
        spinStatusCog(true);
        btn_code_sumbit.text("Stop");
    }
    
	$('input[type=radio][name=auth-mode]').change(function() {
        toggle_login_mode();      
    });

    $("#test-mode[type=checkbox]").switchButton({
        labels_placement: "right",
        on_label: 'Test mode',
        off_label: '',
        checked: is_test
    });

    btn_code_sumbit.click(function() {
        run_code( $('#test-mode[type=checkbox]').is(":checked") );

        if($(this).text() == "Save & Run") $(this).text("Stop")
        else $(this).text("Save & Run")
    });

    $('#test-mode[type=checkbox]').change(function() {
        if( $(this).is(":checked") ) {
            $("#mode-msg").text("You are currently at test mode. Mailbot will simulate your rule but not actually run the rule.");
            run_code(true);
        } 
        else  {
            $("#mode-msg").text("Mailbot will apply your rules to your incoming emails. ");
            run_code(false);
        }   
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
    
    function spinStatusCog(spin) {
        if(spin) {
            document.querySelector(".fa-cog").classList.add("fa-spin");
            document.querySelector(".idle-mark").style.display = "none";
        }
        else {
            document.querySelector(".fa-cog").classList.remove("fa-spin");
            document.querySelector(".idle-mark").style.display = "inline-block";
        }
    }

    function fetch_log() {
        var params = {};
        
        $.post('/fetch_execution_log', params,
            function(res) {
                // $('#donotsend-msg').hide();
                console.log(res);
                
                // Auth success
                if (res.status) {
                    if( log_backup != res['imap_log']){
                        $("#console").html("");
                        append_log(res['imap_log'], false);
                    }
                    
                    log_backup = res['imap_log'];
                }
                else {
                    notify(res, false);
                }
            }
        );
        
        setTimeout(fetch_log, 30 * 1000); // 30 second
    }

    function validateEmail(email) {
        var re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        return re.test(String(email).toLowerCase());
    }    

        btn_login.click(function() {
                var params = {
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
                            $("#btn-code-submit").removeAttr('disabled');
                            $("#btn-test-run").removeAttr('disabled');

                            if ('imap_code' in res) {
                                editor.setValue( res['imap_code'] );
                                spinStatusCog(true);
                            }
                            
                            append_log(res['imap_log'], false)
                            
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

        function run_code(is_dry_run) {
            var params = {
                'email': $("#input-email").val(),
                'code': editor.getValue(),
                'test_run': is_dry_run
            };

            $.post('/run_mailbot', params,
                function(res) {
                    // $('#donotsend-msg').hide();
                    console.log(res);
                    
                    // Auth success
                    if (res.status) {
                        // TODO spin cogs, give feedback it's running
                        if(res['imap_error'])  {
                            // append_log(res['imap_log'], true);

                            spinStatusCog(false);   
                        }
                        else {
                            append_log(res['imap_log'], false)

                            if (editor.getValue() == "") spinStatusCog(false);
                            else spinStatusCog(true);
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
        }

        // btn_test_run.click(function() {
        //     run_code(true);
        // });

        // btn_code_sumbit.click(function() {
        //     run_code(false);
        // });
        // TODO change with change
        // $("#input-email").change(function( event ) {
        //     guess_host( $(this).val() );
        // });
    
        $(".default-text").blur();

    function append_log( log, is_error ) {
        var currentdate = new Date();
        var datetime = (currentdate.getMonth()+1) + "/"
            + currentdate.getDate() + "/" 
            + currentdate.getFullYear() + " @ "  
            + currentdate.getHours() + ":"  
            + currentdate.getMinutes() + ":" 
            + currentdate.getSeconds()
            + " | ";

        datetime = '';

        if(is_error) 
            $( "<p>" + datetime + log.replace(/\n/g , "<br>") + "</p>" ).appendTo( "#console" ).addClass("error");

        else $( "<p>" + datetime + log.replace(/\n/g , "<br>") + "</p>" ).appendTo( "#console" )
            .addClass("info");
    }   

    function guess_host( email_addr ) {
        $("#link-less-secure").attr('href', "");
        $("#rdo-oauth").attr('disabled', "");
        
        if( validateEmail(email_addr) ) {
            $("#password-container").show();
            toggle_login_mode();

            if( email_addr.includes("gmail")) {
                $("#input-host").val("imap.gmail.com");
                $("#link-less-secure").attr('href', "https://myaccount.google.com/lesssecureapps");
                $("#rdo-oauth").removeAttr('disabled');

                $(".oauth").show();
            }
            else {
                $(".oauth").remove();

                $("#rdo-plain").not(':checked').prop("checked", true);
                
                if ( email_addr.includes("yahoo")) $("#input-host").val("imap.mail.yahoo.com");
                else if ( email_addr.includes("csail")) $("#input-host").val("imap.csail.mit.edu");
                else if ( email_addr.includes("mit")) $("#input-host").val("imap.exchange.mit.edu");
                else $("#input-host").val("");

                $(".oauth").hide();
            }
        }
        else $("#password-container").hide();
    }

});