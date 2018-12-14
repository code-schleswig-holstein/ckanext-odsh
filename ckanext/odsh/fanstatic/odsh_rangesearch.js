ckan.module('odsh_rangesearch', function ($)
{
    return {
        initialize: function ()
        {
            var start = $("#ext_startdate")
            var end = $("#ext_enddate")
            var checkbox = $('#check-rangefilter')
            var label = $('#rangesearch-label')
            label.click(function ()
            {
                if (label.hasClass('checked'))
                {
                    start.val('')
                    end.val('')
                }
                if (!label.hasClass('disabled'))
                    $('#date-search-form').submit();
            });

            var updateCheckbox = function ()
            {
                var enable = (start.val() || end.val())
                label.toggleClass('disabled', !enable);
                if (!enable)
                    $('#date-search-form').submit();
            };
            start.change(updateCheckbox)
            end.change(updateCheckbox)
        }
    };
});