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
            $('#ext_score').val(score)
            $("#dataset-search-box-form").submit(); //TODO: use default or inject
        }
    }
    for (let i = 1; i <= 5; i++)
    {
        $('.search-score-' + i).click(search(i));
    }

});


