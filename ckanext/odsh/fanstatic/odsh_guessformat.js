
ckan.module('odsh_guessformat', function ($)
{
    let known_formats = ['pdf', 'rdf', 'txt', 'doc', 'csv']


    let c = $('#field-format')
    let onChange = function (filename)
    {
        let ext = filename.slice((filename.lastIndexOf(".") - 1 >>> 0) + 2).toLowerCase();
        if (ext !== undefined && known_formats.indexOf(ext) > -1)
        {
            c.val(ext.toUpperCase())
        }
    }
    let onRemoved = function ()
    {
        c.val('')
    }

    return {
        initialize: function ()
        {
            if (this.options.formats)
                known_formats = this.options.formats

            this.sandbox.subscribe('odsh_upload_filename_changed', onChange);
            this.sandbox.subscribe('odsh_upload_filename_removed', onRemoved);
        },
        teardown: function ()
        {
            this.sandbox.unsubscribe('odsh_upload_filename_changed', onChange);
            this.sandbox.unsubscribe('odsh_upload_filename_removed', onRemoved);
        },
    };
});