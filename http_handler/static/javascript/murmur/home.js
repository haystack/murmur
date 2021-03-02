$(document).ready(function(){
	console.log("HOME");

	let options = {
		root: null,
		rootMargin: "0px",
		threshold: 0.25,
	}
	
	let slideIn = (entries, observer) => {
		entries.forEach(entry => {
			if (entry.isIntersecting) {
				let elem = entry.target;

				if (entry.intersectionRatio >= 0) {
					elem.classList.add("slide-in");
				}
			}
		});
	};

	let observer = new IntersectionObserver(slideIn, options);
	let descTarget = document.querySelector("#feature-desc");
	let demoTarget = document.querySelector("#feature-demo");
	observer.observe(descTarget);
	observer.observe(demoTarget);
});



	
	
