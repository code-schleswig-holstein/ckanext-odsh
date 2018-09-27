ckan.module('odsh_multiselect', function ($)
{
    return {
        initialize: function ()
        {
            console.log(this.options)
            //ckan destroys uppercase letters ...
            $(this.el[0]).multiselect({
                allSelectedText: this.options.allselectedtext,
                nonSelectedText: this.options.nonselectedtext,
                nSelectedText: this.options.nselectedtext,
                numberDisplayed: 1
            });
        }
    };
});