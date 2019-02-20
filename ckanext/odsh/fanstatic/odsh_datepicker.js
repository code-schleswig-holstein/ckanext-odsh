this.ckan.module('odsh_datepicker', function ($, _)
{
    return {
        initialize: function ()
        {
            var showFormat = "dd.mm.yyyy"
            var opts = {
                format: showFormat,
                // startView: 3,
                // minViewMode: 2,
                // keyboardNavigation: false,
                autoclose: true
            }
            var onChange = function (ev)
            {
                var v = moment(ev.date);
                var fs = 'YYYY-MM-DD';

                switch (ev.target.id)
                {
                    case 'datepicker_start':
                        if (ev.date)
                        {
                            $('#ext_startdate').val(v.format(fs));
                        } else
                        {
                            $('#ext_startdate').val('');
                        }
                        return;
                    case 'datepicker_end':
                        if (ev.date)
                        {
                            $('#ext_enddate').val(v.format(fs));
                        } else
                        {
                            $('#ext_enddate').val('');
                        }
                        return;
                }
            }

            $('#datepicker_start')
                .datepicker(opts)
                .on('changeDate', onChange);
            $('#datepicker_end')
                .datepicker(opts)
                .on('changeDate', onChange);
        }
    }
});
