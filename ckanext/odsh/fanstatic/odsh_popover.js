// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
"use strict";

ckan.module('odsh_popover', function ($)
{
    return {
        initialize: function ()
        {
            this.el.popover({
                       content: this.options.text,
                placement: 'right', html: true,
                trigger:'hover'
            });
        }
    };
});