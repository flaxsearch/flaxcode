
function setCookie(key, val) {
    var expires = ";expires=31 Dec 2010";
    document.cookie = key + "=" + escape(val) + expires;
}

function getCookie(key) {
    if (document.cookie.length > 0) {
        key_start = document.cookie.indexOf( key + "=" );
        if (key_start != -1) {
            val_start = key_start + key.length + 1;
            val_end = document.cookie.indexOf(';', val_start);
            if (val_end == -1)
                val_end = document.cookie.length;
            return unescape(document.cookie.substring(val_start, val_end));
        }
    }
    return "";
}

function CheckBoxListAsString(l) {
    var s = "";
    for (var i=0;i<l.length;++i) {
        if (l[i].checked)
            s = s + "/" + l[i].id;
    }
    return s;
}
   

function saveOptionsToCookie() {
    var formats = document.getElementsByName("format");
    var formats_string = CheckBoxListAsString(formats);
    setCookie("checked_formats", formats_string);
    var cols = document.getElementsByName("col");
    var cols_string = CheckBoxListAsString(cols);
    setCookie("checked_collections", cols_string);
    var sort_by = document.getElementById("sort_by");
    setCookie("sort_by", sort_by.value);
}


function setCheckBoxesFromString(s) {
    var els = s.split("/");
    for (var i=0;i<els.length;++i) {
        var el = document.getElementById(els[i]);
        if (el) {
            el.checked = 1;
        }
    }
}

function populateFormFromCookie() {
    setCheckBoxesFromString(getCookie("checked_formats"));
    setCheckBoxesFromString(getCookie("checked_collections"));
    sort_by = getCookie("sort_by");
    el = document.getElementById("sort_by");
    if (el)
        el.value = sort_by;
}