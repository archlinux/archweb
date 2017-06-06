function setupTypeahead() {
    $('#pkgsearch-field').typeahead({
        source: function(query, callback) {
            $.getJSON('/opensearch/packages/suggest', {q: query}, function(data) {
                callback(data[1]);
            });
        },
        matcher: function(item) { return true; },
        sorter: function(items) { return items; },
        menu: '<ul class="pkgsearch-typeahead"></ul>',
        items: 10,
        updater: function(item) {
            $('#pkgsearch-field').val(item);
            $('#pkgsearch-form').submit();
            return item;
        }
    }).attr('autocomplete', 'off');
    $('#pkgsearch-field').keyup(function(e) {
        if (e.keyCode === 13 &&
                $('ul.pkgsearch-typeahead li.active').size() === 0) {
            $('#pkgsearch-form').submit();
        }
    });
}

function setupKonami(image_src) {
    var konami = new Konami(function() {
        $('#konami').html('<img src="' + image_src + '" alt=""/>');
        setTimeout(function() {
            $('#konami').fadeIn(500);
        }, 500);
        $('#konami').click(function() {
            $('#konami').fadeOut(500);
        });
    });
}
