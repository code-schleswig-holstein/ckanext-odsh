ckan.module('odsh_form', function ($)
{
    return {
        initialize: function ()
        {
            // enable multiselect for input
            if (this.options.multiselect)
                $(this.el[0]).multiselect({
                    allSelectedText: this.options.allselectedtext,
                    nonSelectedText: this.options.nonselectedtext,
                    nSelectedText: this.options.nselectedtext,
                    numberDisplayed: 1
                });
            if (this.options.licensetoggle)
            {
                // toggle input for 'Namensgebung' depending on the selected licence
                // TODO: this implementation should be more generic
                var id = '#field-license';
                var toggle = function ()
                {
                    if ($(id).val().indexOf('dl-by-de/2.0') !== -1)
                    {
                        $('#field-licence-name').prop('disabled', false);
                    } else
                    {
                        $('#field-licence-name').prop('disabled', true);
                    }
                }
                toggle(id)
                $(id).change(toggle);
            }
        }
    };
});