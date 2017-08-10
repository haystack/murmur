$(document).ready(function() {

    var submit_btn = $('#btn-submit'),
        whitelist_check = $('#whitelist-check')[0],
        blacklist_check = $('#blacklist-check')[0],
        user_email = $.trim($('#user_email').text()),
        sender_email = $.trim($('#sender-email').text()),
        group_name = $.trim($('#group-name').text()),
        post_id = $.trim($('#post-id').text()),
        approve_reject = $('input[type=radio][name=approve-reject]'),
        approveDiv = $('#ifApprove')[0],
        rejectDiv = $('#ifReject')[0];

    $('[data-toggle="tooltip"]').tooltip();

    approve_reject.change(function() {
        if (this.value == 'approve') {
            approveDiv.style.display = 'inline';
            rejectDiv.style.display = 'none';
        } else if (this.value == 'reject') {
            approveDiv.style.display = 'none';
            rejectDiv.style.display = 'inline';
        }
    });

    submit_btn.click(function() {
        status_params = {
            'group_name': group_name,
            'post_id': post_id
        };
        var a_r_val = $('input[type=radio][name=approve-reject]:checked').val();
        var post_to_url = a_r_val == 'approve' ? '/approve_post' : '/reject_post';
        var list_url = null;

        if (whitelist_check.checked) list_url = '/whitelist';
        else if (blacklist_check.checked) list_url = '/blacklist';

        if (a_r_val == 'reject') {
            status_params.explanation = $('#explanation').val();
            var tags = [];
            var checked = $('.tag-checks:checkbox:checked');
            checked.each(function() {
                tags.push(this.value);
            });
            if (tags.length > 0) status_params.tags = tags.join(',');
            else status_params.tags = '';
        }


        $.post(post_to_url, status_params, function(status_res) {

            if (status_res.status && list_url != null) {
                var list_params = {
                    'group_name': group_name,
                    'senders': sender_email
                };
                $.post(list_url, list_params, function(list_res) {
                    notify(list_res, true);
                });

            } else notify(status_res, true);

            console.log(status_res);

            if (status_res.status) setTimeout(function() {
                if ($('.reply').length > 0) {
                    location.reload(true);
                } else {
                    window.location = '/mod_queue/' + group_name;
                }
            }, 1000);
        });
    });
});