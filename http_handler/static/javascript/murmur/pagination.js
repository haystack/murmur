var current_page = 1;
allowScroll = true;

function loadMorePosts(current_page){
    $.ajax({
        method: 'POST',
        url: '/post_list?page=' + current_page,
        data: {},
        success: function (data) {
            if ($(data).find("#post-list-table").children().length == 0){
                allowScroll = false;
            } else {
                $("#post-list-table").append($(data).find("#post-list-table").html());
                allowScroll = true;
            }
        },
        error: function (data) {
             alert("Error loading posts.");
        }
    });
}

$(window).scroll(function() {
   var hT = $('#scroll_trigger').offset().top,
       wH = $(window).height(),
       wS = $(this).scrollTop();
   if (wS > (hT-wH)){
        if (allowScroll){
            current_page += 1;
            loadMorePosts(current_page);
            allowScroll = false;
        }
   }
});