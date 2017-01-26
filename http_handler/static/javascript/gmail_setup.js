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
    $('#toggle-all-received').change(function() {
        if(this.checked) {
            $('.received-checkbox').prop('checked', true);
            $('.received-checkbox').parent().parent().css('opacity', '1.0');
            $(this).css('opacity', '1.0');
            emails_checked = true;
        } else {
            $('.received-checkbox').prop('checked', false);
            $('.received-checkbox').parent().parent().css('opacity', '0.5');
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
    var personal_checked = true;
    var social_checked = true;
    var updates_checked = true;
    var promotions_checked = true;
    var forums_checked = true;
    $('.toggle-personal').click(function(){
        if (personal_checked) {
            $('.box-label-personal').prop('checked', false);
            $('.box-label-personal').parent().parent().css('opacity', '0.5');
            personal_checked = false;
        } else {
            $('.box-label-personal').prop('checked', true);
            $('.box-label-personal').parent().parent().css('opacity', '1.0');
            personal_checked = true;
        }
    });
    $('.toggle-social').click(function(){
        if (social_checked) {
            $('.box-label-social').prop('checked', false);
            $('.box-label-social').parent().parent().css('opacity', '0.5');
            social_checked = false;
        } else {
            $('.box-label-social').prop('checked', true);
            $('.box-label-social').parent().parent().css('opacity', '1.0');
            social_checked = true;
        }
    });
    $('.toggle-updates').click(function(){
        if (updates_checked) {
            $('.box-label-updates').prop('checked', false);
            $('.box-label-updates').parent().parent().css('opacity', '0.5');
            updates_checked = false;
        } else {
            $('.box-label-updates').prop('checked', true);
            $('.box-label-updates').parent().parent().css('opacity', '1.0');
            updates_checked = true;
        }
    });
    $('.toggle-promotions').click(function(){
        if (promotions_checked) {
            $('.box-label-promotions').prop('checked', false);
            $('.box-label-promotions').parent().parent().css('opacity', '0.5');
            promotions_checked = false;
        } else {
            $('.box-label-promotions').prop('checked', true);
            $('.box-label-promotions').parent().parent().css('opacity', '1.0');
            promotions_checked = true;
        }
    });
    $('.toggle-forums').click(function(){
        if (forums_checked) {
            $('.box-label-forums').prop('checked', false);
            $('.box-label-forums').parent().parent().css('opacity', '0.5');
            forums_checked = false;
        } else {
            $('.box-label-forums').prop('checked', true);
            $('.box-label-forums').parent().parent().css('opacity', '1.0');
            forums_checked = true;
        }
    });
});