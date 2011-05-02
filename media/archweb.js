/* tablesorter custom parsers for various pages:
 * devel/index.html, mirrors/status.html, todolists/view.html */
if (typeof $.tablesorter !== 'undefined') {
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
            return s.match(/incomplete/i) ? 1 : 0;
        },
        type: 'numeric'
    });
    $.tablesorter.addParser({
        /* sorts numeric, but put '', 'unknown', and '∞' last. */
        id: 'mostlydigit',
        special: ['', 'unknown', '∞'],
        is: function(s, table) {
            var c = table.config;
            return ($.inArray(s, this.special) > -1) || $.tablesorter.isDigit(s, c);
        },
        format: function(s) {
            if ($.inArray(s, this.special) > -1) return Number.MAX_VALUE;
            return $.tablesorter.formatFloat(s);
        },
        type: 'numeric'
    });
    $.tablesorter.addParser({
        /* sorts duration; put '', 'unknown', and '∞' last. */
        id: 'duration',
        re: /^([0-9]+):([0-5][0-9])$/,
        special: ['', 'unknown', '∞'],
        is: function(s) {
            return ($.inArray(s, this.special) > -1) || this.re.test(s);
        },
        format: function(s) {
            if ($.inArray(s, this.special) > -1) return Number.MAX_VALUE;
            var matches = this.re.exec(s);
            if (!matches) return Number.MAX_VALUE;
            return matches[1] * 60 + matches[2];
        },
        type: 'numeric'
    });
    $.tablesorter.addParser({
        id: 'longDateTime',
        re: /^(\d{4})-(\d{2})-(\d{2}) ([012]\d):([0-5]\d)(:([0-5]\d))?( (\w+))?$/,
        is: function(s) {
            return this.re.test(s);
        },
        format: function(s) {
            var matches = this.re.exec(s);
            if (!matches) return 0;
            /* skip group 6, group 7 is optional seconds */
            if (matches[7] == undefined) matches[7] = 0;
            /* The awesomeness of the JS date constructor. Month needs to be
             * between 0-11, because things have to be difficult. */
            var date = new Date(matches[1], matches[2] - 1, matches[3],
                matches[4], matches[5], matches[7]);
            return $.tablesorter.formatFloat(date.getTime());
        },
        type: 'numeric'
    });
    $.tablesorter.addParser({
        id: 'filesize',
        re: /^(\d+(?:\.\d+)?) (bytes?|KB|MB|GB|TB|PB)$/,
        is: function(s) {
            return this.re.test(s);
        },
        format: function(s) {
            var matches = this.re.exec(s);
            if (!matches) return 0;
            var size = parseFloat(matches[1]);
            var suffix = matches[2];

            switch(suffix) {
                case 'byte':
                case 'bytes':
                    return size;
                case 'KB':
                    return size * 1024;
                case 'MB':
                    return size * 1024 * 1024;
                case 'GB':
                    return size * 1024 * 1024 * 1024;
                case 'TB':
                    return size * 1024 * 1024 * 1024 * 1024;
                case 'PB':
                    return size * 1024 * 1024 * 1024 * 1024 * 1024;
            }
        },
        type: 'numeric'
    });
}

/* news/add.html */
function enablePreview() {
    $('#news-preview-button').click(function(event) {
        event.preventDefault();
        $.post('/news/preview/', {
                data: $('#id_content').val(),
                csrfmiddlewaretoken: $('#newsform input[name=csrfmiddlewaretoken]').val()
            },
            function(data) {
                $('#news-preview-data').html(data);
                $('#news-preview').show();
            }
        );
        $('#news-preview-title').html($('#id_title').val());
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
function filter_packages() {
    // start with all rows, and then remove ones we shouldn't show
    var rows = $('#tbody_differences').children();
    var all_rows = rows;
    if (!$('#id_multilib').is(':checked')) {
        rows = rows.not('.multilib').not('.multilib-testing');
    }
    var arch = $('#id_archonly').val();
    if (arch !== 'all') {
        rows = rows.filter('.' + arch);
    }
    if (!$('#id_minor').is(':checked')) {
        // this check is done last because it is the most expensive
        var pat = /(.*)-(.+)/;
        rows = rows.filter(function(index) {
            var cells = $(this).children('td');

            // all this just to get the split version out of the table cell
            var ver_a = cells.eq(2).find('span').text().match(pat);
            if (!ver_a) return true;

            var ver_b = cells.eq(3).find('span').text().match(pat);
            if (!ver_b) return true;

            // first check pkgver
            if (ver_a[1] !== ver_b[1]) return true;
            // pkgver matched, so see if rounded pkgrel matches
            if (Math.floor(parseFloat(ver_a[2])) ==
                Math.floor(parseFloat(ver_b[2]))) return false;
            // pkgrel didn't match, so keep the row
            return true;
        });
    }
    // hide all rows, then show the set we care about
    all_rows.hide();
    rows.show();
    // make sure we update the odd/even styling from sorting
    $('.results').trigger('applyWidgets');
}
function filter_reset() {
    $('#id_archonly').val('both');
    $('#id_multilib').removeAttr('checked');
    $('#id_minor').removeAttr('checked');
    filter_packages();
}

/* todolists/view.html */
function todolist_flag() {
    var link = this;
    $.getJSON(link.href, function(data) {
        if (data.complete) {
            $(link).text('Complete').addClass(
                'complete').removeClass('incomplete');
        } else {
            $(link).text('Incomplete').addClass(
                'incomplete').removeClass('complete');
        }
        /* let tablesorter know the cell value has changed */
        $('.results').trigger('updateCell', $(link).closest('td'));
    });
    return false;
}

/* signoffs.html */
function signoff_package() {
    var link = this;
    $.getJSON(link.href, function(data) {
        if (data.created) {
            var signoff = $('<li>').addClass('signed-username').text(data.user);
            $(link).append(signoff);
        }
        /* update the approved column to reflect reality */
        if (data.approved) {
            var approved = $(link).closest('tr').children('.signoff-no');
            approved.text('Yes').addClass(
                'signoff-yes').removeClass('signoff-no');
        } else {
            var approved = $(link).closest('tr').children('.signoff-yes');
            approved.text('No').addClass(
                'signoff-no').removeClass('signoff-yes');
        }
        $('.results').trigger('updateCell', approved);
    });
    return false;
}
