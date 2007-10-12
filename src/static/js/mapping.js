/* script to insert extra lines into mapping specification part of
   document collection form
*/


/* the 'mappings' container is hardcoded */



var add_mapping = function(path, mapping) {
    var container = document.getElementById('mappings')

    var make_labelled_input = function (txt, name, value) {

        var div = document.createElement('div');
        
        var label = document.createElement('label');
        label.setAttribute('class', 'main_label');
        label.appendChild(document.createTextNode(txt) );
        div.appendChild(label);
        
        var input = document.createElement('input');
        input.setAttribute('name', name);
        input.setAttribute('value', value);
        div.appendChild(input);
        
        container.appendChild(div);

    }
    
    make_labelled_input('Path:', 'path', path);
    make_labelled_input('Mapping:', 'mapping', mapping);
}



/* function suitable for use as an onclick action to add blank mapping inputs */
var add_blank_mapping = function () {
    add_mapping('', '')
}

