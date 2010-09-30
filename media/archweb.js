/* tablesorter custom parsers for various pages:
 * devel/index.html, mirrors/status.html, todolists/view.html */
if(typeof $.tablesorter !== "undefined") {
    $.tablesorter.addParser({
        id: 'pkgcount',
        is: function(s) { return false; },
        format: function(s) {
            var m = s.match(/\d+/);
            return m ? parseInt(m[0]) : 0;
        },
        type: 'numeric'
    });
    $.tablesorter.addParser({
        id: 'todostatus',
        is: function(s) { return false; },
        format: function(s) {
            return s.match(/incomplete/) ? 1 : 0;
        },
        type: 'numeric'
    });
    $.tablesorter.addParser({
        /* sorts numeric, but put '', 'unknown', and '∞' last. */
        id: 'mostlydigit',
        is: function(s,table) {
            var special = ['', 'unknown', '∞'];
            var c = table.config;
            return ($.inArray(s, special) > -1) || $.tablesorter.isDigit(s,c);
        },
        format: function(s) {
            var special = ['', 'unknown', '∞'];
            if($.inArray(s, special) > -1) return Number.MAX_VALUE;
            return $.tablesorter.formatFloat(s);
        },
        type: 'numeric'
    });
    $.tablesorter.addParser({
        /* sorts duration; put '', 'unknown', and '∞' last. */
        id: 'duration',
        is: function(s,table) {
            var special = ['', 'unknown', '∞'];
            return ($.inArray(s, special) > -1) || /^[0-9]+:[0-5][0-9]$/.test(s);
        },
        format: function(s) {
            var special = ['', 'unknown', '∞'];
            if($.inArray(s, special) > -1) return Number.MAX_VALUE;
            matches = /^([0-9]+):([0-5][0-9])$/.exec(s);
            return matches[1] * 60 + matches[2];
        },
        type: 'numeric'
    });
}

/* news/add.html */
function enablePreview() {
    $('#previewbtn').click(function(event) {
        event.preventDefault();
        $.post('/news/preview/',
            { data: $('#id_content').val() },
            function(data) {
            $('#previewdata').html(data);
            $('.news-article').show();
        });
        $('#previewtitle').html($('#id_title').val());
    });
}

/* packages/details.html */
function ajaxifyFiles() {
    $('#filelink').click(function(event) {
        event.preventDefault();
        $.get(this.href, function(data) {
            $('#pkgfilelist').html(data);
        });
    });
}

/* packages/differences.html */
filter_packages = function() {
    // start with all rows, and then remove ones we shouldn't show
    var rows = $(".results tbody tr");
    if(!$('#id_multilib').is(':checked')) {
        rows = rows.not(".multilib");
    }
    var arch = $("#id_archonly").val();
    if(arch !== "all") {
        rows = rows.filter("." + arch);
    }
    if(!$('#id_minor').is(':checked')) {
        // this check is done last because it is the most expensive
        rows = rows.filter(function(index) {
            // all this just to get the split version out of the table cell
            var pat = /(.*)-(.+)/;
            var ver_a = $('td:eq(2) span', this).text().match(pat);
            var ver_b = $('td:eq(3) span', this).text().match(pat);
            // did we match at all?
            if(!ver_a || !ver_b) return true;
            // first check pkgver
            if(ver_a[1] !== ver_b[1]) return true;
            // pkgver matched, so see if rounded pkgrel matches
			if(Math.floor(parseFloat(ver_a[2])) ==
				Math.floor(parseFloat(ver_b[2]))) return false;
            // pkgrel didn't match, so keep the row
            return true;
        });
    }
    // hide all rows, then show the set we care about
    $('.results tbody tr').hide();
    rows.show();
    // make sure we update the odd/even styling from sorting
    $('.results').trigger("applyWidgets");
};
filter_reset = function() {
    $('#id_archonly').val("all");
    $('#id_multilib').removeAttr("checked");
    $('#id_minor').attr("checked", "checked");
    filter_packages();
};

/* todolists/view.html */
todolist_flag = function() {
    var link = this;
    $.getJSON(link.href, function(data) {
        if (data.complete) {
            $(link).text('Complete').addClass('complete').removeClass('incomplete');
        } else {
            $(link).text('Incomplete').addClass('incomplete').removeClass('complete');
        }
    });
    return false;
};
