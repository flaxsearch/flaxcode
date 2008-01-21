/* script to insert extra lines into mapping specification part of
   document collection form
*/

/* the 'mappings' container is hardcoded */

var _pid = 0;

function add_mapping(path, mapping) 
{
    var pid = 'path_input_' + _pid++;
    var m = $('mappings');
    m.appendChild(DIV({}, LABEL({'class':'main_label'}, 'Path:'), 
        INPUT({'class':'input_lesslong', 'name':'path', 'value':path, 'id':pid}),
        ' ',
        A({'href':'javascript:filebrowse(\''+pid+'\')', 
           'class':'browse_link'}, 'browse')));

    m.appendChild(DIV({}, LABEL({'class':'main_label'}, 'Mapping:'), 
        INPUT({'class':'input_long', 'name':'mapping', 'value':mapping})));
}

/* function suitable for use as an onclick action to add blank mapping inputs */
function add_blank_mapping() 
{
    add_mapping('', '')
}

/* open remote file browser for path input "pid" */
function filebrowse(pid)
{
    var w = window.open('/admin/filebrowser', 'filebrowser',
        'width=400,height=500,location=no,menubar=no,toolbar=no,scrollbars=yes,resizable=yes');
    
    w._open_path = $(pid).value;
    w._input_object = $(pid);
}