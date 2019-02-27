$(document).ready(function ()
{
    $('.mylabel').click(function ()
    {
        window.location = $(this).siblings('a').attr('href');
    });

    let search = function (score)
    {
        return function ()
        {
            // $('#label-score-'+score).toggleClass('checked')
            $('#check-score-' + score).prop("checked", !$('#check-score-' + score).prop("checked"));
            //  $('#check-score-'+score).val(1)
            $("#dataset-search-box-form").submit(); //TODO: use default or inject
        }
    }
    for (let i = 1; i <= 5; i++)
    {
        $('.search-score-' + i).click(search(i));
        $('#check-score-' + i).click(function ()
        {
            $("#dataset-search-box-form").submit(); //TODO: use default or inject
        });
    }

});


