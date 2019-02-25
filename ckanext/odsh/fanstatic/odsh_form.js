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
                var id_name = '#field-licenseAttributionByText-value';
                var toggle = function ()
                {
                    if ($(id).val().indexOf('dl-by-de/2.0') !== -1)
                    {
                        $(id_name).prop('disabled', false);
                        if (!$(id_name).val())
                            $(id_name).val($('#field-organizations option:selected').text());
                    } else
                    {
                        $(id_name).prop('disabled', true);
                        $(id_name).val('');
                    }
                }
                toggle(id)
                $(id).change(toggle);
            }
        }
    };
});