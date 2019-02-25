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
            var target = $('#' + this.options.target)
            var showFormat = "dd.mm.yyyy"
            var opts = {
                format: showFormat,
                autoclose: true,
                language: 'de',
                clearBtn: true,
                forceParse: true
            }
            var onChange = function (ev)
            {
                var v = moment(ev.date);
                var fs = 'YYYY-MM-DD';


                if (ev.date)
                {
                    target.val(v.format(fs));
                }
                else
                {
                    target.val('');
                }
            }

            this.el.datepicker(opts)
                .on('changeDate', onChange);
        }
    }
});
