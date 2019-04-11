'use strict';

$(function () {

  // Activate search suggestions for the search bar in the header and for the
  // search bar used in the body.
  $('.site-search input, .search').autocomplete({
    delay: 500,
    html: true,
    minLength: 2,
    source: function (request, response) {
      var url = ckan.SITE_ROOT + '/autocomplete/' + request.term;
      $.getJSON(url)
        .done(function (data) {
          console.log(data);
          response(data['result']);
        });
      }
  });

})