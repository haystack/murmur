import { addRowSelect, handleTagChanges, handleModeChanges } from './modules/tag_subscription.js';

$(document).ready(function(){
    const selectRows = $(".my_row");
    let modeInput = $('input[name="tag-mode"]'),
        selectedTags = $('img[data-type="tag-select"]'), // select elements (block/check icons)
        tags = $(".tag").toArray().map(e => e.innerHTML),
        selectedTagsSet = new Set(selectedTags.toArray()),
        followedTags = new Set(),
        mutedTags = new Set(),
        swapping = false,
        tag_demo_table = $("#tag-subscription-table").DataTable({
        "columns": [ { 'orderable': false}, null, null, null],
        "order": [[1, "asc"]],
        responsive: {
            details: {
                type: 'column',
                target: 'tr'
            }
        },
        searching: false,
        paginate: false,
        info: false,
    });
    
    // Handle actions to demo table
    addRowSelect(selectRows, selectedTagsSet);
    handleTagChanges(selectedTags, tags, mutedTags, followedTags, swapping, updateEmails);
    handleModeChanges(modeInput, selectedTags, swapping);
});

// Changes inbox emails in demo based on changes to tag subscription preferences
function updateEmails(tags, mutedTags, followedTags) {
    const mode = $('input[name="tag-mode"]:checked').val();
    const sampleEmails = $(".sample-email");
    if (mode == "block-mode") {
        sampleEmails.each(function() {
            const emailTags = $(this).children(".label2").toArray().map(x => x.innerHTML);
            const conflictTags = emailTags.filter(x => mutedTags.has(x));
            if (emailTags.length !== 0 && conflictTags.length > 0) {
                this.classList.add("inactive");
            } else {
                $(this).removeClass("inactive");
            }
        });
    } else if (mode == "subscribe-mode") {
        followedTags = new Set(tags.filter(x => !mutedTags.has(x)));
        sampleEmails.each(function() {
            const emailTags = $(this).children(".label2").toArray().map(x => x.innerHTML);
            const desiredTags = emailTags.filter(x => followedTags.has(x));
            if (emailTags.length === 0 || desiredTags.length === 0) {
                this.classList.add("inactive");
            } else {
                $(this).removeClass("inactive");
            }
        });
    }
}