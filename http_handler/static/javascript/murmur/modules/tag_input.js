// AUTOCOMPLETE
function autocomplete(tagInput) {
	/* Listener for tag input box to handle key press actions (e.g. navigating autocomplete tags, navigating added tags) */
	displayTags(tagInput.elem.value, tagInput); // Displays all tags when input string is empty (i.e. "")
	addActiveListTag([], tagInput.currentAutocompleteFocus); // Initially no autocomplete tag item is active/highlighted

	let doc = $(document).get(0);
	tagInput.elem.addEventListener("input", function(e) { // Listen to user input changes
		if (this.value.length === 0) tagInput.currentAutocompleteFocus = -1;
		else tagInput.currentAutocompleteFocus = 0;
		displayTags(this.value, tagInput);
		let tagListItems = geTagListItems(this.id, tagInput),
			tagItems = getTagItems(tagInput.container);
		addActiveListTag(tagListItems, tagInput);
		addActiveTags(tagItems, tagInput);
	});

	if (tagInput.context !== "moderation") {
		// Close lists when someone clicks out of input
		doc.addEventListener("click", (e) => {
			if (e.target != tagInput.elem) {
				tagInput.currentAutocompleteFocus = -1;
				closeAllLists(null, tagInput);
			}
		});
	}
}

// Enclosed functions to pass down the variables from autocomplete call
function displayTags(val=null, tagInput) {
	closeAllLists(null, tagInput);
	// Create container for list items and add to parent container 
	let doc = $(document).get(0);
	let tagList = doc.createElement("UL");
	if (tagInput.context !== "moderation") {
		tagList.setAttribute("id", tagInput.elem.id + "-autocomplete-list");
		tagList.setAttribute("class", "tag-items");
		tagInput.elem.parentNode.appendChild(tagList);
	} else {
		tagList.setAttribute("id", tagInput.elem.id + "-mod-list");
		tagList.setAttribute("class", "tag-items-mod");
		tagInput.elem.parentNode.parentNode.parentNode.appendChild(tagList);
	}
	for (let i = 0; i < tagInput.tags.length; i++) {
		if (!val || tagInput.tags[i]['name'].substr(0, val.length).toUpperCase() == val.toUpperCase()) { // Check if input value matches each word
			if (!tagInput.set.has(tagInput.tags[i]['name'])) { // only autocomplete tags not already added
				// Add autocomplete item container to list 
				let tagListItem = doc.createElement("LI");
				tagListItem.setAttribute("data-tagName", tagInput.tags[i]['name']);
				tagListItem.setAttribute("data-tagColor", tagInput.tags[i]['color']);
				tagListItem.setAttribute("class", "tag-item");

				// Add tag to item container
				let tagItem = doc.createElement("DIV");
				tagItem.setAttribute("class", "tag-label-autocomplete");
				tagItem.setAttribute("style", "background-color: #" + tagInput.tags[i]['color'] + ";");
				tagItem.innerHTML = tagInput.tags[i]['name'];

				tagListItem.appendChild(tagItem);
				
				tagListItem.addEventListener("click", function(e) { // Sets input to selected list item
					let tagName = this.getAttribute("data-tagName"),
						tagColor = this.getAttribute("data-tagColor");
					tagInput.elem.value = "";
					addTagToInput(tagName, tagColor, tagInput);
				});
					tagList.appendChild(tagListItem);
				}
		}
	}
}

// Handles key presses for the tag input
function handleTagInputKeys(e) {
	let tagListItems = geTagListItems(this.elem.id, this),
		tagItems = getTagItems(this.container);
	if (e.keyCode == 40) { // DOWN arrow key 
		e.preventDefault();
		this.currentAutocompleteFocus++;
		addActiveListTag(tagListItems, this);
	} else if (e.keyCode == 38) { // UP arrow key
		e.preventDefault();
		this.currentAutocompleteFocus--;
		addActiveListTag(tagListItems, this);
	} else if (e.keyCode == 37) { // LEFT arrow key
		if (tagItems.length > 0 && this.elem.value.length === 0) {
			e.preventDefault();
			this.currentTagFocus--;
			addActiveTags(tagItems, this);
		}
	} else if (e.keyCode == 39) { // RIGHT arrow key
		if (tagItems.length > 0 && this.elem.value.length === 0) {
			e.preventDefault();
			this.currentTagFocus++;
			addActiveTags(tagItems, this);
		}
	} else if(e.keyCode == 8) { // DELETE arrow key
		if (tagItems.length > 0 && this.currentTagFocus < -1) {
			e.preventDefault();
			deleteSelectedTag(tagItems, this);
		} else if (this.currentTagFocus === -1 && this.elem.value.length < 1) {
			this.currentTagFocus--;
			addActiveTags(tagItems, this);
		}
	} else if (e.keyCode == 13) { // ENTER key simulates click on list item
		e.preventDefault();
		if (tagListItems.length > 0 && this.currentAutocompleteFocus > -1) {
			if (tagListItems) tagListItems[this.currentAutocompleteFocus].click();
		} else if (this.elem.value.length > 0 
					&& tagListItems.length == 0 
					&& this.context !== "moderation") { // check if no autocomplete suggestions -> meaning new tag creation
			let newTagName = this.elem.value,
				newTagColor = generateRandomColor();
				this.elem.value = "";
			addTagToInput(newTagName, newTagColor, this);
		}
	} else if (e.keyCode == 9) { // TAB or SHIFT key simulates click on list item
		removeActiveTags(tagItems);
		this.currentTagFocus = -1;
		if (this.currentAutocompleteFocus > -1) e.preventDefault(); // If no input for adding tag, then allow default tagging to navigate
		if (tagListItems.length > 0 && this.currentAutocompleteFocus > -1) {
			if (tagListItems) tagListItems[this.currentAutocompleteFocus].click();
		} else if (this.elem.value.length > 0 && tagListItems.length == 0) { // check if no autocomplete suggestions -> meaning new tag creation
			let newTagName = this.elem.value,
				newTagColor = generateRandomColor();
				this.elem.value = "";
			addTagToInput(newTagName, newTagColor, this);
		}
		this.currentAutocompleteFocus = -1;
		closeAllLists(null, this.elem);
	}
}

// Create delete tag button on tag labels in tag input
function createDeleteTagBtn(tagName, tagInput) {
	// Add delete tag button to tag label
	let doc = $(document).get(0);
	let tagInputDeleteBtn = doc.createElement("SPAN");
	tagInputDeleteBtn.setAttribute("data-tagName",tagName);
	tagInputDeleteBtn.setAttribute("class","tag-delete-btn ml-1");
	tagInputDeleteBtn.innerHTML = "x";

	tagInputDeleteBtn.addEventListener("click", function(e) {
		deleteTag(this.getAttribute("data-tagName"));
		// Prevents event propagation up DOM tree so parent's (tag container) click event doesn't occur
		e.stopPropagation();
		tagInput.set.delete(tagName); // Delete tags from tag input set
		tagInput.elem.focus();
	});

	return tagInputDeleteBtn;
}

// Deletes the tag label associated to delete button
function deleteTag(tagName) {
	let doc = $(document).get(0);
	let tag = doc.getElementById(tagName + "-tag-input");
	tag.remove()
}

function addTagToInput(tagName, tagColor, tagInput) {
	// Add tag label to tag input list
	let doc = $(document).get(0);
	let tagInputItem = doc.createElement("LI");
	tagInputItem.setAttribute("id", tagName + "-tag-input");
	tagInputItem.setAttribute("data-tagName",tagName);
	tagInputItem.setAttribute("data-tagColor",tagColor);
	tagInputItem.setAttribute("class", "tag-label-input")
	tagInputItem.setAttribute("style", "background-color: #" + tagColor + ";");
	tagInputItem.setAttribute("tabindex", 0);
	tagInputItem.innerHTML = tagName;
	tagInputItem.addEventListener("keydown", handleTagInputKeys.bind(tagInput));
	// Click event for focusing on tags in input
	tagInputItem.addEventListener("click", function () { 
		let tagItems = getTagItems(tagInput.container); // [tags] + [inputElement]
		// ex: tagItems = [tag1,tag2,tag3,input] => target: tag3, index: 2 (-2) => -2 (tagFocus) = 2 (indexOf) - 4 (tagItems.length) as desired
		tagInput.currentTagFocus = tagItems.indexOf(this) - tagItems.length;
		addActiveTags(tagItems, tagInput);
	});

	// Add delete tag to tag label
	let tagInputDeleteBtn = createDeleteTagBtn(tagName, tagInput);
	tagInputItem.appendChild(tagInputDeleteBtn);

	tagInput.list.insertBefore(tagInputItem, tagInput.list.children[tagInput.list.children.length-1]);
	tagInput.set.add(tagName);
	closeAllLists(null, tagInput);
	if (tagInput.context === "moderation") {
		displayTags(tagInput.elem.value, tagInput);
	}
}

function deleteSelectedTag(tagItems, tagInput) {
	removeActiveTags(tagItems);
	if (Math.abs(tagInput.currentTagFocus) > tagItems.length) {
		tagInput.currentTagFocus = -tagItems.length; // handles index beyond first tag elem
	}
	// ex: tagItems = [tag1,tag2,tag3,input] => target: tag3, index: 2 (-2) => 4 (tagItems.length) + -2 (tagFocus) = 2 as desired
	let tag = tagItems[tagItems.length+tagInput.currentTagFocus];
	tag.remove();
	tagInput.set.delete(tag.getAttribute("data-tagName"));
	tagItems.splice(tagItems.length+tagInput.currentTagFocus, 1); // recountruct tag input items after removal
	if (tagItems.length === 1) {
		tagInput.currentTagFocus = -1; // if only one item left, most be tag input elem which needs tagFocus = -1
	}
	addActiveTags(tagItems, tagInput); // focus next item in the list
}

// Makes item active in autocomplete dropdown
function addActiveListTag(items, tagInput) {
	if (items.length === 0 || (tagInput.currentAutocompleteFocus == -1 && items.length === 0)) return false;
	removeActiveListTag(items);
	if (tagInput.currentAutocompleteFocus >= items.length) tagInput.currentAutocompleteFocus = 0;
	if (tagInput.currentAutocompleteFocus < 0) tagInput.currentAutocompleteFocus = (items.length - 1);
	items[tagInput.currentAutocompleteFocus].setAttribute("id","autocomplete-active");
}

// Remove active class from autocomplete items
function removeActiveListTag(items) {
	for (var i = 0; i < items.length; i++) {
		items[i].removeAttribute("id");
	}
}

// Makes item active in added tagged
function addActiveTags(items, tagInput) {
	removeActiveTags(items);
	if (tagInput.currentTagFocus >= -1) { // focus input from tags to (typing) input
		tagInput.currentTagFocus = -1;
		tagInput.elem.focus();
	} else { // blur input (typing) in tag input if on tag and not entering input
		tagInput.elem.blur();
		closeAllLists(null, tagInput);
	}
	if (items.length === 0 || tagInput.currentTagFocus === -1) return false;

	if (Math.abs(tagInput.currentTagFocus) >= items.length) tagInput.currentTagFocus = -items.length;

	items[items.length+tagInput.currentTagFocus].focus();
	items[items.length+tagInput.currentTagFocus].classList.add("tag-focus");
}

// Gets the current autcomplete items
function geTagListItems(inputId, tagInput) {
	let doc = $(document).get(0);
	let items;
	if (tagInput.context !== "moderation") {
		items = doc.getElementById(inputId + "-autocomplete-list");
	} else {
		items = doc.getElementById(inputId + "-mod-list");
	}
	if (items) items = items.getElementsByTagName("LI");
	else items = []
	return items
}

// Gets the current tag items
function getTagItems(tagInputContainer) {
	let doc = $(document).get(0);
	let items = doc.getElementById("tag-input-list");
	if (items) {
		items = [...items.getElementsByClassName("tag-label-input")];
		if (items.length > 0) items.push(tagInputContainer);
	} else items = [];
	return items
}

// Remove active class from tag items
function removeActiveTags(items) {
	for (var i = 0; i < items.length; i++) {
		items[i].blur();
		items[i].classList.remove("tag-focus");
	}
}

// Closes all lists except for selected list
function closeAllLists(element=null, tagInput) {
	let itemsToClose;
	if (tagInput.context !== "moderation") {
		itemsToClose = $(".tag-items");
	} else {
		itemsToClose = $(".tag-items-mod");
	}
	for (let i = 0; i < itemsToClose.length; i++) {
		if (element != itemsToClose[i] && element != tagInput.elem) {
			itemsToClose[i].parentNode.removeChild(itemsToClose[i]);
		}
	}
}

// Generates random colors that valid and are not pure white
function generateRandomColor() {
	let randomColor = Math.floor(Math.random()*16777215).toString(16);
    if(randomColor.length != 6 || randomColor == "ffffff"){ // In any case, the color code is invalid or pure white
        randomColor = generateRandomColor();
    }
    return randomColor;
}

export { autocomplete, getTagItems, removeActiveTags, closeAllLists, displayTags, addTagToInput, handleTagInputKeys };