ckan.module('odsh-map', function ($)
{
    return {
        initialize: function ()
        {
            $('.leaflet-control-zoom-in').prop('title', 'your new title');
        }
    };
});