function bytesToSize(bytes) {
    var sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes == 0) return '0 Byte';
    var i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i];
};

function name_renderer(cell, formatterParams, onRendered) {
    var data = cell.getData();
    if (data.is_dir) 
        return `<a class="type-directory" data-ext="${data.ext}" href="${data.view_url}">${data.name}</a>`;
    else {
        if (data.highlight_url) {
            return `<a class="type-file" data-ext="${data.ext}" href="${data.highlight_url}">${data.name}</a>`;
        } else {
            return `<a class="type-file" data-ext="${data.ext}" href="${data.raw_url}">${data.name}</a>`;
        }
    }
}

function type_renderer(cell, formatterParams, onRendered) {
    var data = cell.getData();
    if (data.is_dir) {
        return "DIR";
    } else {
        return "FILE";
    }
}

function user_renderer(cell, formatterParams, onRendered) {
    var data = cell.getData();
    return data.user + "." + data.group;
}

function modified_renderer(cell, formatterParams, onRendered) {
    var data = cell.getData();
    if (data.modified)
        return moment(data.modified * 1000).fromNow();
    return '';
}

function size_renderer(cell, formatterParams, onRendered) {
    var data = cell.getData();
    if (data.is_file) {
        return bytesToSize(data.size);
    } else {
        return '';
    }
}

function actions_renderer(cell, formatterParams, onRendered) {
    var data = cell.getData();
    var s = '';
    if (data.is_file) {
        s += `<a class="download-link" href="${data.raw_url}" title="Download" alt="Download"><img src="++resource++xmldirector.connector/images/download.png"/></a>`; 
        if (data.highlight_url) {
            s += ` <a class="raw-link" href="${data.highlight_url}" title="View" alt="View"><img src="++resource++xmldirector.connector/images/eye.png"/></a>`;
        }
    }
    return s;
}


function build_table() {        
    var columns = [ 
        {title:"Name", field:"name", width: 450, formatter: name_renderer, headerFilter: true},
        {title:"User", field:"user", formatter: user_renderer, headerFilter: true},
        {title:"Modified", field:"modified", formatter: modified_renderer},
        {title:"Size", field:"size", formatter: size_renderer},
        {title:"Actions", field:"actions", formatter: actions_renderer},
    ];

    var url = URL + '/@@connector-folder-contents?subpath=' + SUBPATH;

    $.ajax({
        url: url,
        dataType: 'json',
        async: false,
        method: 'GET',
        success: function(result) {

        var table = new Tabulator("#files-table", {
            height:450,
            data:result, //assign data to table
            layout:"fitColumns", //fit columns to width of table (optional)
            pagination:"local",
            paginationSize: PAGE_SIZE,
            movableColumns:true,
            columns: columns,
        });
        } 
    });
}


Dropzone.autoDiscover = false;
speed = 250;

$(document).ready(function() {

    build_table();

    new Clipboard('.clipboard');

    $('#action-upload').on('click', function() {
        $('#zip-upload').hide(0); 
        $('#uploadify').toggle(speed); 
    });

    $('#action-new-folder').on('click', function() {
        $('#uploadify').hide(0); 
        $('#zip-upload').hide(0); 
        $('#new-folder').toggle(speed); 
    });

    $('#action-zip-import').on('click', function() {
        $('#uploadify').hide(0); 
        $('#new-folder').hide(0); 
        $('#zip-upload').toggle(speed); 
    });


    $('.legend-close').on('click', function() {
        $(this).parents('fieldset').hide();
    });

    $("#dropzone").dropzone({ 
        url: UPLOAD_URL,
        maxFilesize: 50,
        addRemoveLinks: false,
        parallelUploads: 1
    });

    $('.modified').each(function(index, item) {
        var modified = $(item).data('modified');
        var modified_str = moment(modified).fromNow();
        $(item).html(modified_str);
    });

    $('.size').each(function(index, item) {
        var size= $(item).data('size');
        $(item).html(bytesToSize(size));
    });
});
