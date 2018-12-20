"use strict";

function bytesToSize(bytes) {
    var sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes == 0) return '0 Byte';
    var i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i];
};

function name_renderer(cell, formatterParams, onRendered) {
    var data = cell.getData();
    if (data.is_dir)  {
        return `<a class="type-directory" data-subpath="${data.full_path}">${data.name}</a>`;
        return `<a class="type-directory" data-ext="${data.ext}" href="${data.view_url}">${data.name}</a>`;
    }
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
    if (data.user != '' && data.group != '')
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


function notify(s) {
    $('#table-message').fadeOut(0, 0, function () {
        $(this).html(s);
        $(this).show();
        $(this).fadeOut(2500);
    });
}

function setup_click_handlers() {

    $('#table-refresh').on('click', function(event) {
        load_data_into_table();
    });

    $('.type-directory,.type-directory-bc').on('click', function(event) {
        event.preventDefault();
        var subpath = $(this).data('subpath');
        window.history.pushState(subpath, subpath, `${URL}/view/${subpath}`);
        load_data_into_table(subpath);
    })

    $('.rename-link').on('click', function(event) {

        $('#files-table').block();
        event.preventDefault()

        var name = $(this).data('name');        
        var new_name = prompt("Enter new name", name);
        if (new_name == null || new_name =="") {
            return false
        }

        var resource_name = `${SUBPATH}/${name}`;
        var url = `${URL}/@@connector-rename?resource_name:unicode=${resource_name}&new_name:unicode=${new_name}`; 


        $.ajax({
            url: url,
            dataType: 'json',
            async: true,
            method: 'POST',
            success: function(result) {

                var rows = table.getRows();
                for (var i=0; i<rows.length; i++) {
                    var row = rows[i];
                    var data = row.getData();
                    if (data.name == name) {
                        table.updateRow(row, {name: new_name});
                        notify(`Renamed ${resource_name} to ${new_name}`);
                        $('#files-table').unblock();
                        break;
                    }
                }
            } ,
            error: function(result) {
                notify(`Error renaming ${resource_name}`);
                $('#files-table').unblock();
            }
        });

        return false;
    });

    $('.remove-link').on('click', function(event) {

        $('#files-table').block();
        event.preventDefault()
        
        var name = $(this).data('name');        
        var resource_name = `${SUBPATH}/${name}`;

        var url = `${URL}/@@connector-remove?resource_name:unicode=${resource_name}`; 

        $.ajax({
            url: url,
            dataType: 'json',
            async: true,
            method: 'POST',
            success: function(result) {

                /* remove entry from table */
                var rows = table.getRows();
                for (var i=0; i<rows.length; i++) {
                    var row = rows[i];
                    var data = row.getData();
                    if (data.name == name) {
                        row.delete();
                        $('#files-table').unblock();
                        notify(`Deleted sucessfully: ${resource_name}`); 
                        break;
                    }
                }
            } ,
            error: function(result) {
                notify(`Error deleting ${resource_name}`);
                $('#files-table').unblock();
            }
        });

        return false;
    });
}


var table = null;

function build_table() {        

    var columns = [ 
        {title:"Name", field:"name", width: 450, formatter: name_renderer, headerFilter: true},
        {title:"User", field:"user", formatter: user_renderer, headerFilter: true, align: "center"},
        {title:"Modified", field:"modified", formatter: modified_renderer, align: "center"},
        {title:"Size", field:"size", formatter: size_renderer, align: "center"},
        {title:"Actions", field:"actions", formatter: actions_renderer, align: "right"},
    ];

    table = new Tabulator("#files-table", {
        height:450,
        layout:"fitColumns", //fit columns to width of table (optional)
        pagination:"local",
        paginationSize: PAGE_SIZE,
        movableColumns:true,
        columns: columns
    });

    $('#table-message').prependTo('.tabulator-footer')
    load_data_into_table();
}


function load_data_into_table(subpath=null)  {

    var url = '';
    if (subpath != null) 
        url = URL + '/@@connector-folder-contents?subpath:unicode=' + subpath;
    else
        url = URL + '/@@connector-folder-contents?subpath:unicode=' + SUBPATH;

    table.setData(url).
        then(function() {
            $('#pagination').show()
            setup_click_handlers();
            update_breadcrumbs(subpath == null ? SUBPATH : subpath);
        });
}


function update_breadcrumbs(subpath) {
    var parts = subpath.split('/');
    parts  = parts.filter(el => el.length > 0);
    var s = '<a class="type-directory-bc root" data-subpath="">root<a>';
    for (var i=0; i<parts.length; i++) {
        var this_subpath = parts.slice(0, i+1).join('/');
        s += '/';
        s += `<a class="type-directory-bc" data-subpath="${this_subpath}">${parts[i]}</a>`;
    }
    $('#breadcrumbs-generated').html(s);
    setup_click_handlers();
}


Dropzone.autoDiscover = false;
var speed = 250;

$(document).ready(function() {

    build_table();

    new Clipboard('.clipboard');

    $('#action-upload').on('click', function() {
        $('#new-folder').hide(0); 
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
        parallelUploads: 3,
        queuecomplete()  {
            load_data_into_table();
        },
        complete(file) {
            this.removeFile(file);
        }
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
