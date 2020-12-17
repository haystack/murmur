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
			tagInput = $("#tag-input").get(0);
			post = $("#btn-post");
			subjectInput = $("#new-post-subject").get(0);
			subjectInputHeight = 38;
			tags = django_tag_data["tags"];
			tagInputList = $(".tag-input-list").get(0);
			tagInputTagSet = new Set();
			tagInfo = []
			
	insert_post = 
		function(params){
			console.log(tagInputTagSet.length);
			console.log(tagInput.value.length);
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
	tagInput.addEventListener('focus', (event) => {
		autocomplete(tagInput,tags);    
	});

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
	let currentFocus = -1;

	displayTags(tagInput.value);
	addActive([]);

	tagInput.addEventListener("input", function(e) { // Listen to user input changes
		if (this.value.length === 0) currentFocus = -1;
		else currentFocus = 0;
		displayTags(this.value);
		let items = getItems(this.id);
		addActive(items);
	});
	
	tagInput.addEventListener("keydown", handleTagInputKeys);

	// Gets the current autcomplete items
	function getItems(inputId) {
		let items = document.getElementById(inputId + "autocomplete-list");
		if (items) items = items.getElementsByTagName("LI");
		else items = []
		return items
	}

	// Makes item active throw
	function addActive(items) {
		if (items.length === 0 || (currentFocus == -1 && items.length === 0)) return false;
		removeActive(items);

		if (currentFocus >= items.length) currentFocus = 0;
		if (currentFocus < 0) currentFocus = (items.length - 1);
		
		items[currentFocus].setAttribute("id","autocomplete-active");
	}

	// Remove active class from autocomplete items
	function removeActive(items) {
		for (var i = 0; i < items.length; i++) {
			items[i].removeAttribute("id");
		}
	}

	// Handles key presses for the tag input
	function handleTagInputKeys(e) {
		let items = getItems(tagInput.id);
		if (e.keyCode == 40) { // DOWN arrow key 
			e.preventDefault();
			currentFocus++;
			addActive(items);
		} else if (e.keyCode == 38) { // UP arrow key
			e.preventDefault();
			currentFocus--;
			addActive(items);
		} else if (e.keyCode == 13) { // ENTER key simulates click on list item
			e.preventDefault();
			if (items.length > 0 && currentFocus > -1) {
				if (items) items[currentFocus].click();
			} else if (tagInput.value.length > 0 && items.length == 0) { // check if no autocomplete suggestions -> meaning new tag creation
				let newTagName = tagInput.value;
					newTagColor = generateRandomColor();
				tagInput.value = "";
				addTagToInput(newTagName, newTagColor);
			}
		} else if (e.keyCode == 9) { // TAB key simulates click on list item
			if (currentFocus > -1) e.preventDefault(); // If no input for adding tag, then allow default tagging to navigate
			if (items.length > 0 && currentFocus > -1) {
				if (items) items[currentFocus].click();
			} else if (tagInput.value.length > 0 && items.length == 0) { // check if no autocomplete suggestions -> meaning new tag creation
				let newTagName = tagInput.value;
					newTagColor = generateRandomColor();
				tagInput.value = "";
				addTagToInput(newTagName, newTagColor);
			}
			currentFocus = -1;
			closeAllLists();
		}
	}

  	// Close lists when someone clicks out of input
	$(document).click((e) => {
		currentFocus = -1;
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
			if (!tagInputTagSet.has(tags[i]['name'])){
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
	tagInputItem = document.createElement("LI");
	tagInputItem.setAttribute("id", tagName + "-tag-input")
	tagInputItem.setAttribute("data-tagName",tagName);
	tagInputItem.setAttribute("data-tagColor",tagColor);
	tagInputItem.setAttribute("class", "tag-label-input")
	tagInputItem.setAttribute("style", "background-color: #" + tagColor + ";");
	tagInputItem.innerHTML = tagName;

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

		// Delete tags from tag input set
		tagInputTagSet.delete(tagName);
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
	
// Closes all lists except for selected list
function closeAllLists(element) {
	let itemsToClose = $(".tag-items");
	for (let i = 0; i < itemsToClose.length; i++) {
		if (element != itemsToClose[i] && element != tagInput) {
			itemsToClose[i].parentNode.removeChild(itemsToClose[i]);
		}
	}
}
	
