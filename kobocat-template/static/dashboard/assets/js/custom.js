+ function($) {
	// header nav on scoll
	navigationScroll();
	$(window).resize(function() {
	    navigationScroll();  
	    console.log("foo")
	   	

	});
	function navigationScroll(){
	   if ($(window).width() > 767) {
	    	var mHeight = $(".get-height").height();
	    	var mHeight = mHeight - 50;
	    	var headerTop = $(".header-top").height();
	    	var headerTop = headerTop +  12;
	    	$(window).bind('scroll', function() {
	    	  if ($(window).scrollTop() > mHeight) {
	    	    $('.header-outer-wrap').addClass("hide-top-header");
	    	    $('.header-outer-wrap').css({
	    	    	"top" : -headerTop
	    	    });
	    	    
	    	  } else {
	    	    $('.header-outer-wrap').removeClass("hide-top-header");
	    	    $('.header-outer-wrap').css("top", "");
	    	  }
	    	});
	   }else{
	   		$('.header-outer-wrap').css("top", "");
	   } 
	};
	// header nav end
	// couter up start
	$('.counter').counterUp({
	    delay: 10,
	    time: 1000
	});
	// couter end 


	 $('[data-toggle="tooltip"]').tooltip();






      // owl start integration
      $("#owl-brand").owlCarousel({
        items: 6,
        autoPlay: true
      });
      // owl end integration


      // request a demo page

      domianNavigation();
      $(window).resize(function() {
          domianNavigation();  
      });
      function domianNavigation(){
         if ($(window).width() < 768) {
            $(".header-top").addClass("mobile-nav")
         }     
      };

      $(".domain-nav").on("click", function(){
      	  // $(".mobile-nav").toggleClass( "show" );
      	  $(".mobile-nav").slideToggle( "slow" );
      })


    

}(jQuery);

