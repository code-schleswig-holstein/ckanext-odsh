this.ckan.module('odsh_datepicker', function ($, _)
{
    return {
        initialize: function ()
        {
            var showFormat = "dd.mm.yyyy";
            var serverFormat = 'YYYY-MM-DD';
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
                    format: showFormat
                };
            var target = $('#' + this.options.target)
            var opts = {
                format: showFormat,
                autoclose: true,
                language: 'de',
                clearBtn: true,
                forceParse: false
            }
            var onChange = function (ev)
            {
                var dateString = $(ev.target).val()
                var date = moment(dateString, "DD.MM.YYYY", true)
                var isValid = date.isValid() && (dateString.length == 10)
                if (isValid)
                {
                    var serverDate = date.format(serverFormat);
                    target.val(serverDate);
                }
                else
                {
                    target.val(dateString);
                }
            }
            var onClear = function (ev)
            {
                target.val('');
            }

            this.el.datepicker(opts)
                .on('changeDate', onChange);
            this.el.datepicker(opts)
                .on('clearDate', onClear);
        }
    }
});
