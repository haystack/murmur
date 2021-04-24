// Click listener for the whole row to be clickable and toggle blocking/subscribing
function addRowSelect(selectRows, selectedTagsSet) {
	selectRows.each((index, elem) => {
		elem.addEventListener("click", (e) => {
			if (!selectedTagsSet.has(e.target)) elem.firstElementChild.firstElementChild.click()
		});
    });
}

// Select column with block/checkmark icons to select rows
function handleTagChanges(selectedTags, tags, mutedTags, followedTags, swapping, updateEmails) {
    selectedTags.each((index, elem) => {
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
            if (updateEmails !== undefined) updateEmails(tags, mutedTags, followedTags);
		})
	});
}

// Toggles visibility of tags based on tag mode change
function handleModeChanges(modeInput, selectedTags, swapping) {
    modeInput.change(function() {
		const mode = $('input[name="tag-mode"]:checked').val();
		selectedTags.each((index, elem) => {
			if (mode == "block-mode") {
				elem.setAttribute("src", "/static/css/third-party/images/block.svg");
			} else if (mode == "subscribe-mode") {
				elem.setAttribute("src", "/static/css/third-party/images/check.svg");
			}
			swapping = true;
			elem.click()
		});
	});
}

export { addRowSelect, handleTagChanges, handleModeChanges };