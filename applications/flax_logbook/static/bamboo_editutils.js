
function bamboo_doc_edit_ready() {
    // bind autocompleter to each filter field
    $(".bam_edit .bam_filter").each(function(i) {
        bind_autocomplete(this);
    });
    
    // bind handler to controls
    // FIXME add hover tips
    $("a[href=bam_field_dup]").click(handle_bam_field_dup);
    $("a[href=bam_field_del]").click(handle_bam_field_del);
    
    // init the menu, binding the function to insert a new field
    bam_menu_init("bam_field_choice", function(item, target) {
        var fname = $(item).attr("title");
        var url = "../../fields/" + escape(fname) + "/getnew";
        $.get(url, null, function(data, textStatus) {
            var newtr = $(data);
            bind_field_controls(newtr);
            $(target).closest("tr").after(newtr);
        }, "html");
    });
    
    // hide the message box (and make it click-to-hide)
    $("#bam_message").hide().click(function() {
        $(this).fadeOut();
    });

    // bind the textarea resizer
    $(".bam_resize_toggle").click(handle_resize_toggle);
    
}

function bind_autocomplete(el) {
    var url = "../../terms/" + el.name;
    $(el).autocomplete(url, {'matchCase':true, 'autoFill':true, 'delay':200});
}

function handle_bam_field_dup(event) {
    // duplicate a field
    event.preventDefault();
    
    // get the innermost parent tr
    var parent = $(this).closest("tr");
    var pclone = parent.clone();
    pclone.find("input").each(function(i) {
        $(this).val("");
        if ($(this).hasClass("bam_filter_input")) {
            bind_autocomplete(this);
        }
    });
    pclone.find("textarea").each(function(i) {
        $(this).text("");
    });
    
    bind_field_controls(pclone);
    pclone.insertAfter(parent);
}

function bind_field_controls(el) {
    // set up jquery bindings for newly-added field

    el.find(".bam_filter").each(function(i) {
        bind_autocomplete(this);
    });

    el.find("a[href=bam_field_del]").click(handle_bam_field_del);
    el.find("a[href=bam_field_dup]").click(handle_bam_field_dup);

    bam_bind_menu_handler(el.find("a[href=bam_field_choice]"), "bam_field_choice");
}

function handle_bam_field_del(event) {
    // delete a field
    event.preventDefault();
    var pa = $(this).closest("tr");
    var val = pa.find(':input').val();
    if (val == "" || confirm("Remove field?")) {
        pa.replaceWith("");
    }
}

function handle_resize_toggle(event) {
    event.preventDefault();
    $(this).prev().toggleClass("bam_large");
}

function show_message(text, fadeout) {
    $("#bam_message").text(text).fadeIn("fast", 
    function() {
        if (fadeout) {
            $(this).fadeOut("slow");
        }
    });
}

function bamboo_doc_savecon() {
    var formdata = $("form").serializeArray();
    var response = validate_formdata(formdata);
    if (response == true) {
        $.ajax({"type": "POST",
                "url": "../../docs",
                "data": {"json": JSON.stringify(formdata)},
                "success": function(data, textstatus) {
                    $("#bam_doccount").text(data);
                    $("input[name=id]").attr("disabled", "true");
                    show_message("Document saved", true);
                },
                "error":  function(req, status, exception) {
                    alert(status);
                }
        });
    }
}

function bamboo_doc_savenew() {
    var jdata = JSON.stringify($("form").serializeArray());
    $.ajax({"type": "POST",
            "url": "../../docs",
            "data": {"json": jdata},
            "success": function() {
                window.location = "../../new/doc/edit";  // HACK!
            },
            "error":  function(req, status, exception) {
                alert(status);
            }
    });
}

function bamboo_doc_duplicate() {
    $("input[name=id]").removeAttr("readonly").val('').focus();
}

function bamboo_doc_cancel() {
    window.history.back();
}

function validate_formdata(formdata) {
    return true;
}

