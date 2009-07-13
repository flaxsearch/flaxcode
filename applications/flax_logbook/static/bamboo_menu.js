/*
 * Copyright (c) 2009 Lemur Consulting Ltd
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */

/// FIXME!
/// the popup object must be a UL list with an id <menu_name>
/// targets are A elements with HREF = <menu_name>

// object storing popup data, keyed by menu_name. Each item has two properties:
// "timer" - setTimeout handle for fading popup out
// "target" - the element which triggered the popup
var _menu_data = {};

function bam_do_fade_popup(menu_name) {
    /// Fade out the named popup
    $("#" + menu_name).fadeOut("fast");
    _menu_data[menu_name].timer = null;
}

function bam_schedule_fade_popup(menu_name) {
    /// Set a timeout for the named menu to fade out
    if (_menu_data[menu_name].timer == null) {
        _menu_data[menu_name].timer = setTimeout(
            'bam_do_fade_popup("' + menu_name + '")', 500);    
    }
}

function bam_cancel_fade_popup(menu_name) {
    /// Cancel the fadeout for the named popup
    if (_menu_data[menu_name].timer) {
        clearTimeout(_menu_data[menu_name].timer);
        _menu_data[menu_name].timer = null;
        return true;
    }
    return false;
}

function bam_bind_menu_handler(items, menu_name) {
    /// Bind a menu handler for <menu_name> to the jquery <items> object.
    items.hover(function(event) {
        bam_cancel_fade_popup(menu_name);
    }, function(event) {
        bam_schedule_fade_popup(menu_name);
    }).click(function(event) {
        event.preventDefault();
        var offs = $(this).offset();
        var pop = $("#" + menu_name).css({'top': offs.top, 'left': offs.left - 150});
        _menu_data[menu_name].target = $(this);
        if (! bam_cancel_fade_popup(menu_name)) {
            pop.fadeIn("fast");
        }
    });
}

function bam_menu_init(menu_name, callback) {
    /// Init the popup menu with the id <menu_name>
    /// <callback> is a function which will be called when a menu item is selected
    /// It takes two parameters, <item> and <target>, both JQuery objects
    ///   <item> is the selected LI object
    ///   <target> is the A object which triggered the popup

    _menu_data[menu_name] = {'timer': null, 'target': null};
    bam_bind_menu_handler($("a[href=" + menu_name + "]"), menu_name);

    $("#" + menu_name).hide().hover(function(event) {
        bam_cancel_fade_popup(menu_name);
    }, function() {
        bam_schedule_fade_popup(menu_name);
    });
        
    $("#" + menu_name + " li").hover(function(event) {
        $(this).addClass("bam_popup_item_selected");
    }, function(event) {
        $(this).removeClass("bam_popup_item_selected");
    }).click(function(event) {
        $(this).removeClass("bam_popup_item_selected");
        var menu_item = $(this);
        var menu_target = $(_menu_data[menu_name].target);
        $("#" + menu_name).hide();
        callback(menu_item, menu_target);
    });
}
