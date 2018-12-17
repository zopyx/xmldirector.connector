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
    if (data.can_remove) {
            s += ` <a class="remove-link" data-name="${data.name}" href="${data.highlight_url}" title="Remove" alt="Remove"><img src="++resource++xmldirector.connector/images/remove.png"/></a>`;

            s += ` <a class="rename-link" data-name="${data.name}" href="${data.highlight_url}" title="Rename" alt="Rename"><img src="++resource++xmldirector.connector/images/rename.png"/></a>`;

    }
    return s;
}


table = null;

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

            table = new Tabulator("#files-table", {
                height:450,
                data:result, //assign data to table
                layout:"fitColumns", //fit columns to width of table (optional)
                pagination:"local",
                paginationSize: PAGE_SIZE,
                movableColumns:true,
                columns: columns,
            });

            /* move #pagination into tabulator footer */
            $('#pagination').prependTo('.tabulator-footer');
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

    $('#page_size').on('change', function() {
        var page_size = $(this).val();
        table.setPageSize(page_size);
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

    $('.rename-link').on('click', function(event) {

        event.preventDefault()

        var name = $(this).data('name');        

        var new_name = prompt("Enter new name", name);
        if (new_name == null || new_name =="") {
            return false
        }
        new_name = escape(new_name);

        var resource_name = escape(`${SUBPATH}/${name}`);
        url = `${URL}/@@connector-rename?resource_name=${resource_name}&new_name=${new_name}`; 

        $.ajax({
            url: url,
            dataType: 'json',
            async: false,
            method: 'POST',
            success: function(result) {

                /* remove entry from table */
                var rows = table.getRows();
                for (i=0; i<rows.length; i++) {
                    var row = rows[i];
                    var data = row.getData();
                    console.log(data);
                    if (data.name == name) {
/*                        table.updateData({id: i, name: "oo"});
                        alert(`Renamed ${resource_name} to ${new_name}`); 
                        */
                        break;
                    }
                }
            } ,
            error: function(result) {
                alert(`Error renaming ${resource_name}`);
            }
        });

        return false;
    });

    $('.remove-link').on('click', function(event) {

        event.preventDefault()

        var name = $(this).data('name');        
        var resource_name = escape(`${SUBPATH}/${name}`);

        url = `${URL}/@@connector-remove?resource_name=${resource_name}`; 

        $.ajax({
            url: url,
            dataType: 'json',
            async: false,
            method: 'POST',
            success: function(result) {

                alert(`Deleted sucessfully: ${resource_name}`); 

                /* remove entry from table */
                var rows = table.getRows();
                for (i=0; i<rows.length; i++) {
                    var row = rows[i];
                    var data = row.getData();
                    if (data.name == name) {
                        row.delete();
                        break;
                    }
                }
            } ,
            error: function(result) {
                alert(`Error deleting ${resource_name}`);
            }
        });


        return false;
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
