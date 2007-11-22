/* script to insert extra lines into mapping specification part of
   document collection form
*/

/* the 'mappings' container is hardcoded */

function add_mapping(path, mapping) 
{
    var container = document.getElementById('mappings')

    function make_labelled_input(txt, name, value) 
    {
        var div = document.createElement('div');
        var label = document.createElement('label');
        label.className = 'main_label';
        label.appendChild(document.createTextNode(txt) );
        div.appendChild(label);

        var input = document.createElement('input');
        input.className = 'input_long';
        input.name = name;
        input.value = value;
        div.appendChild(input);
        
        container.appendChild(div);
    }
    
    make_labelled_input('Path:', 'path', path);
    make_labelled_input('Mapping:', 'mapping', mapping);
}



/* function suitable for use as an onclick action to add blank mapping inputs */
function add_blank_mapping() 
{
    add_mapping('', '')
}

