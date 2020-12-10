$(document).ready(function(){
    let selectRows = $(".my_row");
        modeInput = $('input[name="tag-mode"]');
        selectTags = $('img[data-type="tag-select"]'); // select elements (block/check icons)
        sampleEmails = $(".sample-email");
        tags = $(".tag").toArray().map(e => e.innerHTML);
        selectTagsSet = new Set(selectTags.toArray());
        followedTags = new Set();
        mutedTags = new Set();
        swapping = false;
        tag_demo_table = $("#tag-demo-table").DataTable({
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

    console.log(tags);
    
    // Click listener for the whole row to be clickable and toggle blocking/subscribing
	selectRows.each((index, elem) => {
		elem.addEventListener("click", (e) => {
			if (!selectTagsSet.has(e.target)) elem.firstElementChild.firstElementChild.click()
		});
    });
    
    // Select column with block and checkmark icons to select rows
	selectTags.each((index, elem) => {
		elem.addEventListener("click", function() {
			const mode = $('input[name="tag-mode"]:checked').val();
			const tag = elem.parentNode.nextElementSibling.firstElementChild;
			elem.toggleAttribute("checked");
			elem.classList.toggle("inactive");

			if (!swapping) {
				const isSelected = elem.hasAttribute("checked")
				if (mode == "block-mode") {
					if (isSelected) mutedTags.add(tag.innerHTML);
					else mutedTags.delete(tag.innerHTML);
				} else if (mode == "subscribe-mode") {
					if (isSelected) mutedTags.delete(tag.innerHTML);
					else mutedTags.add(tag.innerHTML);
				}
			}
            swapping = false;
            updateEmails();
		})
	});
	
	// Toggles visibility of tags based on tag mode change
	modeInput.change(function() {
		const mode = $('input[name="tag-mode"]:checked').val();
		selectTags.each((index, elem) => {
			if (mode == "block-mode") {
				elem.setAttribute("src", "/static/css/third-party/images/block.svg");
			} else if (mode == "subscribe-mode") {
				elem.setAttribute("src", "/static/css/third-party/images/check.svg");
			}
			swapping = true;
			elem.click()
		});
	});
});

function updateEmails() {
    const mode = $('input[name="tag-mode"]:checked').val();
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
                desiredTags = emailTags.filter(x => followedTags.has(x));
            if (emailTags.length === 0 || desiredTags.length === 0) {
                this.classList.add("inactive");
            } else {
                $(this).removeClass("inactive");
            }
        });
    }
}