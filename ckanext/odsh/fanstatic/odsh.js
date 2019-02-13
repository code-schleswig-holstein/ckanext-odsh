$(document).ready(function() {
    $('.mylabel').click(function() {
	window.location = $(this).siblings('a').attr('href');
    });

    // $('#tooltip').tooltip(show)
});


