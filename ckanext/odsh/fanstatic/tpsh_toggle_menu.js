"use strict";

ckan.module('tpsh_toggle_menu', function ($) {
    return {
        initialize: function () {
            $.proxyAll(this, /_on/);
            this.el.on('click', this._onClick);
        },
        
        _onClick: function(event) {
            var element = $("body");
            var className = "menu-modal"
            if (element.hasClass(className)){
                element.removeClass(className)
            }
            else {
                element.addClass(className);
            }
        }
    };
});