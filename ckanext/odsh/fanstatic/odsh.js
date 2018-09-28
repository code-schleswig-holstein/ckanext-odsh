$(document).ready(function() {
    $('.filter_checkbox').change(function() {
	window.location = $(this).siblings().first().attr('href');
    });
});


