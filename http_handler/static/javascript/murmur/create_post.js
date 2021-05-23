import { autocomplete, getTagItems, removeActiveTags, closeAllLists, handleTagInputKeys } from './modules/tag_input.js';

$(document).ready(function(){

	let editor = CKEDITOR.replace( 'new-post-text', {
		extraAllowedContent: 'strong[onclick]'
	} );

	CKEDITOR.instances['new-post-text'].on('contentDom', function() {
		this.document.on('click', function(event){
			tagInput.currentAutocompleteFocus = -1;
			closeAllLists(null, tagInput);
		 });
	});
	
	let userName = $.trim($('#user_email').text());
	let post = $("#btn-post");
	let subjectInput = {
		'elem': $("#new-post-subject").get(0),
		'height': 38,
	}
	let tagInfo = [];
	const tagInput = {
		context: "autocomplete",
		container: $(".tag-input-container").get(0),
		elem: $("#tag-input").get(0),
		tags: django_tag_data["tags"],
		list: $("#tag-input-list").get(0),
		set: new Set(), // used to more efficiently determine if a certain tag exists 
		currentAutocompleteFocus: -1, 
		currentTagFocus: -1 // negative index of tag input item currently focused ex: [tag1,tag2,tag3,{tagInput}], {} = focused
	}

	const insert_post = 
		function(params){
			if (tagInput.set.size == 0 && tagInput.elem.value.length > 0) {
				alert("Please press enter/tab after tag in tag input to add/create tag or remove any input if no tags desired.");
			} else {
				let subjectText = $("#new-post-subject").val();
				tagInput.set.forEach((tagName) => {
					let tagElement = document.getElementById(tagName+"-tag-input");
					let tagColor = tagElement.getAttribute("data-tagColor");
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
	tagInput.elem.addEventListener("focus", (event) => {
		tagInput.currentTagFocus = -1;
		removeActiveTags(getTagItems(tagInput.container));
		autocomplete(tagInput);    
	});

	/* Listener for tag input box to handle key press actions (e.g. navigating autocomplete tags, navigating added tags) */
	tagInput.elem.addEventListener("keydown", handleTagInputKeys.bind(tagInput));

	/* Listener for subject line to resize according to the size of the text */
	subjectInput.elem.addEventListener("input", resizeSubjectInput.bind(subjectInput), false);

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

// Resizes the subject input element
function resizeSubjectInput() {
	if (this.elem.value == '') {
		this.elem.setAttribute("style", "height:" + this.height + "px;overflow-y:hidden;");
	} else {
		this.elem.setAttribute("style", "height:" + (this.elem.scrollHeight) + "px;overflow-y:hidden;");
		this.elem.style.height = "auto";
		this.elem.style.height = (this.elem.scrollHeight) + "px";
	}
}
	
