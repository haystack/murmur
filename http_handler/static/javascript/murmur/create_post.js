$(document).ready(function(){

	let editor = CKEDITOR.replace( 'new-post-text', {
		extraAllowedContent: 'strong[onclick]'
	} );

	CKEDITOR.instances['new-post-text'].on('contentDom', function() {
		this.document.on('click', function(event){
			 closeAllLists();
		 });
	});

	const userName = $.trim($('#user_email').text());
			tagInputContainer = $(".tag-input-container").get(0);
			tagInput = $("#tag-input").get(0);
			post = $("#btn-post");
			subjectInput = $("#new-post-subject").get(0);
			subjectInputHeight = 38;
			tags = django_tag_data["tags"];
			tagInputList = $("#tag-input-list").get(0);
			tagInputTagSet = new Set();
			tagInfo = [];
			currentAutocompleteFocus = -1;
			currentTagFocus = -1; // negative index of tag input item currently focused ex: [tag1,tag2,tag3,{tagInput}], {} = focused
			
	insert_post = 
		function(params){
			if (tagInputTagSet.size == 0 && tagInput.value.length > 0) {
				alert("Please press enter/tab after tag in tag input to add/create tag or remove any input if no tags desired.");
			} else {
				let subjectText = $("#new-post-subject").val();
				tagInputTagSet.forEach((tagName) => {
					let tagElement = document.getElementById(tagName+"-tag-input");
						tagColor = tagElement.getAttribute("data-tagColor");
					subjectText = "[" + tagName + "]" + subjectText.substr(0);
					tagInfo.push({"name": tagName, "color": tagColor});
				});
				params.msg_text = CKEDITOR.instances['new-post-text'].getData();
				params.subject = subjectText
				params.group_name = $("#new-post-to").text();
				params.poster_email = params.requester_email;
				params.tag_info = JSON.stringify(tagInfo);
				$.post('/insert_post', params, 
					function(res){
						notify(res, true);
						
						if(res.status){
							setTimeout(function () {
								window.location.href = "/post_list?group_name=" + params.group_name;
							}, 600);
						}
					}
				);
		  	}	
		};

	
	bind_buttons();

	/* Listener for tag input box to autocomplete once it clicked and focused on */
	tagInput.addEventListener("focus", (event) => {
		currentTagFocus = -1;
		removeActiveTags(getTagItems());
		autocomplete();    
	});

	/* Listener for tag input box to handle key press actions (e.g. navigating autocomplete tags, navigating added tags) */
	tagInput.addEventListener("keydown", handleTagInputKeys);

	/* Listener for subject line to resize according to the size of the text */
	subjectInput.addEventListener("input", resizeInput, false);

	function bind_buttons() {
 		post.unbind("click");
 		
 		post.bind("click");
		let params = {'requester_email': userName};
 		let add_post = bind(insert_post, params);
		
		post.click(add_post);
	}

});

/* To avoid closure */	
function bind(fnc, val ) {
	return function () {
		return fnc(val);
	};
}

function notify(res, on_success){
	if(!res.status){
		noty({text: "Error: " + res.code, dismissQueue: true, timeout:2000, force: true, type: 'error', layout: 'topRight'});
	}else{
		if(on_success){
			noty({text: "Success!", dismissQueue: true, timeout:2000, force: true, type:'success', layout: 'topRight'});
		}
	}
}


// AUTOCOMPLETE
function autocomplete() {
	displayTags(tagInput.value); // Displays all tags when input string is empty (i.e. "")
	addActiveAutocomplete([]); // Initially no autocomplete tag item is active/highlighted

	tagInput.addEventListener("input", function(e) { // Listen to user input changes
		if (this.value.length === 0) currentAutocompleteFocus = -1;
		else currentAutocompleteFocus = 0;
		displayTags(this.value);
		let autocompleteItems = getAutocompleteItems(this.id);
			tagItems = getTagItems();
		addActiveAutocomplete(autocompleteItems);
		addActiveTags(tagItems);
	});

  	// Close lists when someone clicks out of input
	$(document).click((e) => {
		currentAutocompleteFocus = -1;
		closeAllLists(e.target);
	});
}

function displayTags(val=null) {
	closeAllLists();
	// Create container for list items and add to parent container 
	let autocompleteList = document.createElement("UL");
	autocompleteList.setAttribute("id", tagInput.id + "autocomplete-list");
	autocompleteList.setAttribute("class", "tag-items");
	tagInput.parentNode.appendChild(autocompleteList);
	for (let i = 0; i < tags.length; i++) {
		if (!val || tags[i]['name'].substr(0, val.length).toUpperCase() == val.toUpperCase()) { // Check if input value matches each word
			if (!tagInputTagSet.has(tags[i]['name'])) { // only autocomplete tags not already added
				// Add autocomplete item container to list 
				autocompleteItem = document.createElement("LI");
				autocompleteItem.setAttribute("data-tagName", tags[i]['name']);
				autocompleteItem.setAttribute("data-tagColor", tags[i]['color']);
				autocompleteItem.setAttribute("class", "tag-item");

				// Add tag to item container
				tagItem = document.createElement("DIV");
				tagItem.setAttribute("class", "tag-label-autocomplete");
				tagItem.setAttribute("style", "background-color: #" + tags[i]['color'] + ";");
				tagItem.innerHTML = tags[i]['name'];

				autocompleteItem.appendChild(tagItem);
				
				autocompleteItem.addEventListener("click", function(e) { // Sets input to selected list item
					let tagName = this.getAttribute("data-tagName");
						tagColor = this.getAttribute("data-tagColor");
					tagInput.value = "";
					addTagToInput(tagName, tagColor);
				});
					autocompleteList.appendChild(autocompleteItem);
				}
		}
	}
}

function addTagToInput(tagName, tagColor) {
	// Add tag label to tag input list
	let tagInputItem = document.createElement("LI");
	tagInputItem.setAttribute("id", tagName + "-tag-input")
	tagInputItem.setAttribute("data-tagName",tagName);
	tagInputItem.setAttribute("data-tagColor",tagColor);
	tagInputItem.setAttribute("class", "tag-label-input")
	tagInputItem.setAttribute("style", "background-color: #" + tagColor + ";");
	tagInputItem.setAttribute("tabindex", 0);
	tagInputItem.innerHTML = tagName;
	tagInputItem.addEventListener("keydown", handleTagInputKeys);
	// Click event for focusing on tags in input
	tagInputItem.addEventListener("click", function () { 
		let tagItems = getTagItems(); // [tags] + [inputElement]
		// ex: tagItems = [tag1,tag2,tag3,input] => target: tag3, index: 2 (-2) => -2 (tagFocus) = 2 (indexOf) - 4 (tagItems.length) as desired
		currentTagFocus = tagItems.indexOf(this) - tagItems.length;
		addActiveTags(tagItems);
	});

	// Add delete tag to tag label
	let tagInputDeleteBtn = createDeleteTagBtn(tagName, "input");
	tagInputItem.appendChild(tagInputDeleteBtn);

	tagInputList.insertBefore(tagInputItem, tagInputList.children[tagInputList.children.length-1]);
	tagInputTagSet.add(tagName);
	closeAllLists();
}

// Generates random colors that valid and are not pure white
function generateRandomColor() {
	let randomColor = Math.floor(Math.random()*16777215).toString(16);
    if(randomColor.length != 6 || randomColor == "ffffff"){ // In any case, the color code is invalid or pure white
        randomColor = generateRandomColor();
    }
    return randomColor;
}


// Create delete tag button on tag labels in tag input
function createDeleteTagBtn(tagName) {
	// Add delete tag button to tag label
	tagInputDeleteBtn = document.createElement("SPAN");
	tagInputDeleteBtn.setAttribute("data-tagName",tagName);
	tagInputDeleteBtn.setAttribute("class","tag-delete-btn ml-1");
	tagInputDeleteBtn.innerHTML = "x";

	tagInputDeleteBtn.addEventListener("click", function(e) {
		deleteTag(this.getAttribute("data-tagName"));
		// Prevents event propagation up DOM tree so parent's (tag container) click event doesn't occur
		e.stopPropagation();
		tagInputTagSet.delete(tagName); // Delete tags from tag input set
		tagInput.focus();
	});

	return tagInputDeleteBtn;
}

// Deletes the tag label associated to delete button
function deleteTag(tagName) {
	let tag = document.getElementById(tagName + "-tag-input");
	tag.remove()
}

function resizeInput() {
	if (subjectInput.value == '') {
		subjectInput.setAttribute("style", "height:" + subjectInputHeight + "px;overflow-y:hidden;");
	} else {
		subjectInput.setAttribute("style", "height:" + (subjectInput.scrollHeight) + "px;overflow-y:hidden;");
		subjectInput.style.height = "auto";
		subjectInput.style.height = (subjectInput.scrollHeight) + "px";
	}
}

// Gets the current autcomplete items
function getAutocompleteItems(inputId) {
	let items = document.getElementById(inputId + "autocomplete-list");
	if (items) items = items.getElementsByTagName("LI");
	else items = []
	return items
}

// Gets the current tag items
function getTagItems() {
	let items = document.getElementById("tag-input-list");
	if (items) {
		items = [...items.getElementsByClassName("tag-label-input")];
		if (items.length > 0) items.push(tagInputContainer);
	} else items = [];
	return items
}

// Makes item active in autocomplete dropdown
function addActiveAutocomplete(items) {
	if (items.length === 0 || (currentAutocompleteFocus == -1 && items.length === 0)) return false;
	removeActiveAutocomplete(items);

	if (currentAutocompleteFocus >= items.length) currentAutocompleteFocus = 0;
	if (currentAutocompleteFocus < 0) currentAutocompleteFocus = (items.length - 1);

	items[currentAutocompleteFocus].setAttribute("id","autocomplete-active");
}

// Remove active class from autocomplete items
function removeActiveAutocomplete(items) {
	for (var i = 0; i < items.length; i++) {
		items[i].removeAttribute("id");
	}
}

// Makes item active in added tagged
function addActiveTags(items) {
	removeActiveTags(items);
	if (currentTagFocus >= -1) { // focus input from tags to (typing) input
		currentTagFocus = -1;
		$("#tag-input").focus();
	} else { // blur input (typing) in tag input if on tag and not entering input
		$("#tag-input").blur();
		closeAllLists();
	}
	if (items.length === 0 || currentTagFocus === -1) return false;

	if (Math.abs(currentTagFocus) >= items.length) currentTagFocus = -items.length;
	items[items.length+currentTagFocus].focus();
	items[items.length+currentTagFocus].classList.add("tag-focus");
}

// Remove active class from tag items
function removeActiveTags(items) {
	for (var i = 0; i < items.length; i++) {
		items[i].blur();
		items[i].classList.remove("tag-focus");
	}
}

// Handles key presses for the tag input
function handleTagInputKeys(e) {
	let autocompleteItems = getAutocompleteItems(tagInput.id);
		tagItems = getTagItems();
	if (e.keyCode == 40) { // DOWN arrow key 
		e.preventDefault();
		currentAutocompleteFocus++;
		addActiveAutocomplete(autocompleteItems);
	} else if (e.keyCode == 38) { // UP arrow key
		e.preventDefault();
		currentAutocompleteFocus--;
		addActiveAutocomplete(autocompleteItems);
	} else if (e.keyCode == 37) { // LEFT arrow key
		if (tagItems.length > 0 && tagInput.value.length === 0) {
			e.preventDefault();
			currentTagFocus--;
			addActiveTags(tagItems);
		}
	} else if (e.keyCode == 39) { // RIGHT arrow key
		if (tagItems.length > 0 && tagInput.value.length === 0) {
			e.preventDefault();
			currentTagFocus++;
			addActiveTags(tagItems);
		}
	} else if(e.keyCode == 8) { // DELETE arrow key
		if (tagItems.length > 0 && currentTagFocus < -1) {
			e.preventDefault();
			deleteSelectedTag(tagItems);
		} else if (currentTagFocus === -1) {
			currentTagFocus--;
			addActiveTags(tagItems);
		}
	} else if (e.keyCode == 13) { // ENTER key simulates click on list item
		e.preventDefault();
		if (autocompleteItems.length > 0 && currentAutocompleteFocus > -1) {
			if (autocompleteItems) autocompleteItems[currentAutocompleteFocus].click();
		} else if (tagInput.value.length > 0 && autocompleteItems.length == 0) { // check if no autocomplete suggestions -> meaning new tag creation
			let newTagName = tagInput.value;
				newTagColor = generateRandomColor();
			tagInput.value = "";
			addTagToInput(newTagName, newTagColor);
		}
	} else if (e.keyCode == 9) { // TAB or SHIFT key simulates click on list item
		removeActiveTags(tagItems);
		currentTagFocus = -1;
		if (currentAutocompleteFocus > -1) e.preventDefault(); // If no input for adding tag, then allow default tagging to navigate
		if (autocompleteItems.length > 0 && currentAutocompleteFocus > -1) {
			if (autocompleteItems) autocompleteItems[currentAutocompleteFocus].click();
		} else if (tagInput.value.length > 0 && autocompleteItems.length == 0) { // check if no autocomplete suggestions -> meaning new tag creation
			let newTagName = tagInput.value;
				newTagColor = generateRandomColor();
			tagInput.value = "";
			addTagToInput(newTagName, newTagColor);
		}
		currentAutocompleteFocus = -1;
		closeAllLists();
	}

	function deleteSelectedTag(tagItems) {
		removeActiveTags(tagItems);
		if (Math.abs(currentTagFocus) > tagItems.length) currentTagFocus = -tagItems.length; // handles index beyond first tag elem
		// ex: tagItems = [tag1,tag2,tag3,input] => target: tag3, index: 2 (-2) => 4 (tagItems.length) + -2 (tagFocus) = 2 as desired
		let tag = tagItems[tagItems.length+currentTagFocus];
		tag.remove();
		tagInputTagSet.delete(tag.getAttribute("data-tagName"));
		tagItems.splice(tagItems.length+currentTagFocus, 1); // recountruct tag input items after removal
		if (tagItems.length === 1) currentTagFocus = -1; // if only one item left, most be tag input elem which needs tagFocus = -1
		addActiveTags(tagItems); // focus next item in the list
	}
}
	
// Closes all lists except for selected list
function closeAllLists(element) {
	let itemsToClose = $(".tag-items");
	for (let i = 0; i < itemsToClose.length; i++) {
		if (element != itemsToClose[i] && element != tagInput) {
			itemsToClose[i].parentNode.removeChild(itemsToClose[i]);
		}
	}
}
	
