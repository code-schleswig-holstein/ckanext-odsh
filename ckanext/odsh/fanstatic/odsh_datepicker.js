this.ckan.module('odsh_datepicker', function ($, _)
{
    return {
        initialize: function ()
        {
            if (!$.fn.datepicker.dates['de'])
                $.fn.datepicker.dates['de'] = {
                    days: ["Sonntag", "Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag"],
                    daysShort: ["Son", "Mon", "Die", "Mit", "Don", "Fre", "Sam"],
                    daysMin: ["So", "Mo", "Di", "Mi", "Do", "Fr", "Sa"],
                    months: ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"],
                    monthsShort: ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"],
                    today: "Heute",
                    monthsTitle: "Monate",
                    clear: "Löschen",
                    weekStart: 1,
                    format: "dd.mm.yyyy"
                };
            var showFormat = "dd.mm.yyyy"
            var opts = {
                format: showFormat,
                // startView: 3,
                // minViewMode: 2,
                // keyboardNavigation: false,
                autoclose: true,
                language: 'de'
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
