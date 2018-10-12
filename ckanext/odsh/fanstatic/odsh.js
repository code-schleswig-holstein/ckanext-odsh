$(document).ready(function() {
    $('.mylabel').click(function() {
	console.log($(this).siblings());
	window.location = $(this).siblings('a').attr('href');
    });
});


