$(document).ready( function() {
    $("#tabs").tabs({
        activate: function (event, ui) {
            var active = $('#tabs').tabs('option', 'active');
        }
    });

    $("#slider").slider({
        max: slider_max,
        min: 0,
        value: 0,
        slide: function(event, ui) {
            var current_val = 0;
            while (current_val <= ui.value) {
                $('.freq-' + map[current_val]).prop("checked", false);
                $('.item-freq-' + map[current_val]).css('opacity', '0.5');
                current_val++;
            }
            while (current_val <= max) {
                $('.freq-' + map[current_val]).prop("checked", true);
                $('.item-freq-' + map[current_val]).css('opacity', '1.0');
                current_val++;
            }
        }
    });
    $('#toggle-all-contacts').change(function() {
        if(this.checked) {
            $('.contacts-checkbox').prop('checked', true);
            $('.contacts-checkbox').parent().parent().css('opacity', '1.0');
            $(this).css('opacity', '1.0');
            contacts_checked = true;
        } else {
            $('.contacts-checkbox').prop('checked', false);
            $('.contacts-checkbox').parent().parent().css('opacity', '0.5');
            $(this).css('opacity', '0.5');
            contacts_checked = false;
        }
    });
    $('#toggle-all-personal').change(function() {
        if(this.checked) {
            $('.box-label-personal').prop('checked', true);
            $('.box-label-personal').parent().parent().css('opacity', '1.0');
            $(this).css('opacity', '1.0');
            emails_checked = true;
        } else {
            $('.box-label-personal').prop('checked', false);
            $('.box-label-personal').parent().parent().css('opacity', '0.5');
            $(this).css('opacity', '0.5');
            emails_checked = false;
        }
    });
    $('#toggle-all-social').change(function() {
        if(this.checked) {
            $('.box-label-social').prop('checked', true);
            $('.box-label-social').parent().parent().css('opacity', '1.0');
            $(this).css('opacity', '1.0');
            emails_checked = true;
        } else {
            $('.box-label-social').prop('checked', false);
            $('.box-label-social').parent().parent().css('opacity', '0.5');
            $(this).css('opacity', '0.5');
            emails_checked = false;
        }
    });
    $('#toggle-all-forums').change(function() {
        if(this.checked) {
            $('.box-label-forums').prop('checked', true);
            $('.box-label-forums').parent().parent().css('opacity', '1.0');
            $(this).css('opacity', '1.0');
            emails_checked = true;
        } else {
            $('.box-label-forums').prop('checked', false);
            $('.box-label-forums').parent().parent().css('opacity', '0.5');
            $(this).css('opacity', '0.5');
            emails_checked = false;
        }
    });
    $('#toggle-all-updates').change(function() {
        if(this.checked) {
            $('.box-label-updates').prop('checked', true);
            $('.box-label-updates').parent().parent().css('opacity', '1.0');
            $(this).css('opacity', '1.0');
            emails_checked = true;
        } else {
            $('.box-label-updates').prop('checked', false);
            $('.box-label-updates').parent().parent().css('opacity', '0.5');
            $(this).css('opacity', '0.5');
            emails_checked = false;
        }
    });
    $('#toggle-all-promotions').change(function() {
        if(this.checked) {
            $('.box-label-promotions').prop('checked', true);
            $('.box-label-promotions').parent().parent().css('opacity', '1.0');
            $(this).css('opacity', '1.0');
            emails_checked = true;
        } else {
            $('.box-label-promotions').prop('checked', false);
            $('.box-label-promotions').parent().parent().css('opacity', '0.5');
            $(this).css('opacity', '0.5');
            emails_checked = false;
        }
    });


    $(":checkbox").change(function() {
        name = $(this).attr('name')
        if(this.checked) {
            $(this).parent().parent().css('opacity', '1.0');
            $("input[name='"+name+"']").prop('checked', true);
            $("input[name='"+name+"']").parent().parent().css('opacity', '1.0');
        } else {
            $(this).parent().parent().css('opacity', '0.5');
            $("input[name='"+name+"']").prop('checked', false);
            $("input[name='"+name+"']").parent().parent().css('opacity', '0.5');
        }
    });
});