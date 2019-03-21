ckan.module('odsh_form', function ($)
{
    return {
        initialize: function ()
        {
            // enable multiselect for input
            if (this.options.multiselect)
            {
                var multi = $(this.el[0])
                if (multi)
                {
                    multi.multiselect({
                        allSelectedText: this.options.allselectedtext,
                        nonSelectedText: this.options.nonselectedtext,
                        nSelectedText: this.options.nselectedtext,
                        numberDisplayed: 1,
                        onChange: function (option, checked, select)
                        {
                            var values = $('#field-groups option:selected')
                                .map(function (a, item) { return item.value; }).get().join(',')
                            $('#field-groups-value').val(values);
                        }
                    });
                }
            }

            if (this.options.licensetoggle)
            {
                // toggle input for 'Namensgebung' depending on the selected licence
                // TODO: this implementation should be more generic
                var id = '#field-license';
                var id_name = '#field-licenseAttributionByText-value';
                var autofill=this.options.autofill
                var toggle = function ()
                {
                    let text = $(id + ' option:selected').text()
                    if (text.indexOf('Namensnennung') !== -1)
                    {
                        $(id_name).prop('disabled', false);
                        if (!$(id_name).val()&&autofill)
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