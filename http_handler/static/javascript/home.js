$(document).ready(function(){
    
	var now = 0;
	var array = [
				 "/static/images/murmurations/6507188799_8474f9775a_o.jpg",
				 "/static/images/murmurations/2115134127_9c074ca2b2_o.jpg",
    			 "/static/images/murmurations/4227228_6bdfe3543e_o.jpg",
    			 "/static/images/murmurations/4227243_a0587ccefe_o.jpg",
    			 "/static/images/murmurations/4483577_fec76ad00f_o.jpg",
    			 "/static/images/murmurations/4483546_9a1a9906e4_o.jpg", 
    			 "/static/images/murmurations/4483522_fbbf80a6ca_o.jpg",
    			 "/static/images/murmurations/4483398_dbd42c5993_o.jpg" 
    			  ];
    			  
   	var about = ["<a href='https://www.flickr.com/photos/58618501@N02/6507188799'>Image</a> by <a href='https://www.flickr.com/photos/58618501@N02'>Karen Fletcher</a>",
   				 "<a href='https://www.flickr.com/photos/howzey/2115134127/'>Image</a> by <a href='https://www.flickr.com/photos/howzey'>Paul</a>",
   				 "<a href='https://www.flickr.com/photos/stevemac/4227228'>Image</a> by <a href='https://www.flickr.com/photos/stevemac'>steve mcnicholas</a>",
   				"<a href='https://www.flickr.com/photos/stevemac/4227243'>Image</a> by <a href='https://www.flickr.com/photos/stevemac'>steve mcnicholas</a>",
   				"<a href='https://www.flickr.com/photos/stevemac/4483577'>Image</a> by <a href='https://www.flickr.com/photos/stevemac'>steve mcnicholas</a>",
   				"<a href='https://www.flickr.com/photos/stevemac/4483546'>Image</a> by <a href='https://www.flickr.com/photos/stevemac'>steve mcnicholas</a>",
   				"<a href='https://www.flickr.com/photos/stevemac/4483522'>Image</a> by <a href='https://www.flickr.com/photos/stevemac'>steve mcnicholas</a>",
   				"<a href='https://www.flickr.com/photos/stevemac/4483398'>Image</a> by <a href='https://www.flickr.com/photos/stevemac'>steve mcnicholas</a>",
   				 ]
    			  
	function getRandomInt(min, max) {
    	return Math.floor(Math.random() * (max - min + 1)) + min;
	}
	
	var val = getRandomInt(0,7);
    $('body').css({'background-image': 'url("' + array[val] + '")'});
    $('#image-attrib').html(about[val]);

	if ($('.home-left').length > 0) {
		window.setInterval(function() {
			var val = getRandomInt(0,7);
	        $('body').css({'background-image': 'url("' + array[val] + '")'});
	        $('#image-attrib').html(about[val]);
		}, 12000);
	}
	

});



	
	
