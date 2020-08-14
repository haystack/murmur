$(document).ready(function(){
	
	CKEDITOR.replace( 'new-post-text' );
			
	const userName = $.trim($('#user_email').text());
			tagInput = $("#tagInput").get(0);
			post = $("#btn-post");
			subjectInput = $("#new-post-subject").get(0);
			subjectInputHeight = 38;
			tags = django_tag_data["tags"];
			tagInputList = $(".tag-input-list").get(0);
			tagInputTagSet = new Set();
			
	insert_post = 
		function(params){
			let subjectText = $("#new-post-subject").val();
			tagInputTagSet.forEach((tagName) => subjectText = "[" + tagName + "]" + subjectText.substr(0)) 
			params.msg_text = CKEDITOR.instances['new-post-text'].getData();
			params.subject = subjectText
            params.group_name = $("#new-post-to").text();
			params.poster_email = params.requester_email;
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
		};

	
	bind_buttons();
	autocomplete(tagInput,tags);

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
function autocomplete(inp, arr) {
	// inp = inpt element, arr = list of items to autocomplete from 
	let currentFocus;

	inp.addEventListener("input", function(e) { // Listen to user input changes
		let autocompleteList, autocompleteItem, val = this.value;
		closeAllLists(); // Close any list that's currently open
		if (!val) { return false;}

		currentFocus = 0;

		// Create container for list items and add to parent container 
		autocompleteList = document.createElement("UL");
		autocompleteList.setAttribute("id", this.id + "autocomplete-list");
		autocompleteList.setAttribute("class", "tag-items");
		this.parentNode.appendChild(autocompleteList);

		for (let i = 0; i < arr.length; i++) {
		  if (arr[i]['name'].substr(0, val.length).toUpperCase() == val.toUpperCase()) { // Check if input value matches each word
			
			// Add autocomplete item container to list 
			autocompleteItem = document.createElement("LI");
			autocompleteItem.setAttribute("data-tagName", arr[i]['name']);
			autocompleteItem.setAttribute("data-tagColor", arr[i]['color']);
			autocompleteItem.setAttribute("class", "tag-item");

			// Add tag to item container
			tagItem = document.createElement("DIV");
			tagItem.setAttribute("class", "tag-label-autocomplete");
			tagItem.setAttribute("style", "background-color: #" + arr[i]['color'] + ";");
			tagItem.innerHTML = arr[i]['name'];

			autocompleteItem.appendChild(tagItem);
			
			autocompleteItem.addEventListener("click", function(e) { // Sets input to selected list item
				let tagName = this.getAttribute("data-tagName");
					tagColor = this.getAttribute("data-tagColor");
				inp.value = "";
			
				if (!tagInputTagSet.has(tagName)){
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
				}
				closeAllLists();
			});
			autocompleteList.appendChild(autocompleteItem);
		  }
		}

		let items = getItems(this.id);
		addActive(items);
	});
	
	inp.addEventListener("keydown", function(e) {
		let items = getItems(this.id);

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
			if (currentFocus > -1) {
				if (items) items[currentFocus].click();
		  	}
		} else if (e.keyCode == 9) { // TAB key simulates click on list item
			if (inp.value.length > 0) e.preventDefault(); // If no input for adding tag, then allow default tagging to navigate
				
			if (currentFocus > -1) {
				if (items) items[currentFocus].click();
			}
		} 
	});

	// Gets the current autcomplete items
	function getItems(inputId) {
		let items = document.getElementById(inputId + "autocomplete-list");
		if (items) items = items.getElementsByTagName("LI");
		return items
	}

	// Makes item active throw
	function addActive(items) {
		if (items.length === 0) return false;
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

	// Closes all lists except for selected list
	function closeAllLists(element) {
		let itemsToClose = $(".tag-items");
		for (let i = 0; i < itemsToClose.length; i++) {
			if (element != itemsToClose[i] && element != inp) {
				itemsToClose[i].parentNode.removeChild(itemsToClose[i]);
			}
		}
	}

  	// Close lists when someone clicks out of input
	$(document).click((e) => closeAllLists(e.target));
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
	
	
