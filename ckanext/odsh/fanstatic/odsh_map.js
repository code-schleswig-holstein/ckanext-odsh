ckan.module('odsh-map', function ($)
{
    return {
        initialize: function ()
        {
            console.log('ini')
            $('.leaflet-control-zoom-in').prop('title', 'your new title');
        }
    };
});