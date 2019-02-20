// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
"use strict";

ckan.module('odsh_popover', function ($)
{
    return {
        initialize: function ()
        {
            var trigger = 'hover'
            if (this.options.trigger == 'custom')
                trigger = 'custom'
            var p = this.el.popover({
                content: this.options.text,
                placement: 'right', html: true,
                trigger: trigger,
                animation: false
            })
            if (trigger == 'custom')
            {
                p.on('mouseenter', function ()
                {
                    var _this = this;
                    $(this).popover('show');
                    $('.popover').on('mouseleave', function ()
                    {
                        $(_this).popover('hide');
                    });
                }).on('mouseleave', function ()
                {
                    var _this = this;
                    setTimeout(function ()
                    {
                        if (!$('.popover:hover').length)
                        {
                            $(_this).popover('hide');
                        }
                    }, 300);
                });
            }
        }
    };
});