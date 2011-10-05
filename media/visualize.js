function packages_treemap(chart_id, orderings, default_order) {
    var jq_div = $(chart_id),
        color = d3.scale.category20();
        key_func = function(d) { return d.key; },
        value_package_count = function(d) { return d.count; };

    var treemap = d3.layout.treemap()
        .size([jq_div.width(), jq_div.height()])
        /*.sticky(true)*/
        .value(value_package_count)
        .sort(function(a, b) { return a.key < b.key; })
        .children(function(d) { return d.data; });

    var cell_html = function(d) {
        if (d.children) {
            return "";
        }
        return "<span>" + d.name + ": " + treemap.value()(d) + "</span>";
    };

    var d3_div = d3.select(jq_div.get(0));

    var prop_px = function(prop, offset) {
        return function(d) {
            var dist = d[prop] + offset;
            if (dist > 0) return dist + "px";
            else return "0px";
        };
    };

    var cell = function() {
        /* the -1 offset comes from the border width we use in the CSS */
        this.style("left", prop_px("x", 0)).style("top", prop_px("y", 0))
            .style("width", prop_px("dx", -1)).style("height", prop_px("dy", -1));
    };

    var fetch_for_ordering = function(order) {
        d3.json(order.url, function(json) {
            var nodes = d3_div.data([json]).selectAll("div").data(treemap.nodes, key_func);
            /* start out new nodes in the center of the picture area */
            var w_center = jq_div.width() / 2;
            var h_center = jq_div.height() / 2;
            nodes.enter().append("div")
                .attr("class", "treemap-cell")
                .attr("title", function(d) { return d.name; })
                .style("left", w_center + "px").style("top", h_center + "px")
                .style("width", "0px").style("height", "0px")
                .style("display", function(d) { return d.children ? "none" : null; })
                .html(cell_html);
            nodes.transition().duration(1500)
                .style("background-color", function(d) { return d.children ? null : color(d[order.color_attr]); })
                .call(cell);
            nodes.exit().transition().duration(1500).remove();
        });
    };

    /* start the callback for the default order */
    fetch_for_ordering(orderings[default_order]);

    var make_scale_button = function(name, valuefunc) {
        var button_id = chart_id + "-" + name;
        /* upon button click, attach new value function and redraw all boxes
         * accordingly */
        d3.select(button_id).on("click", function() {
            d3_div.selectAll("div")
                .data(treemap.value(valuefunc), key_func)
                .html(cell_html)
                .transition().duration(1500).call(cell);

            /* drop off the '#' sign to convert id to a class prefix */
            d3.selectAll("." + chart_id.substring(1) + "-scaleby")
                .classed("active", false);
            d3.select(button_id).classed("active", true);
        });
    };

    /* each scale button tweaks our value, e.g. net size function */
    make_scale_button("count", value_package_count);
    make_scale_button("flagged", function(d) { return d.flagged; });
    make_scale_button("csize", function(d) { return d.csize; });
    make_scale_button("isize", function(d) { return d.isize; });

    var make_group_button = function(name, order) {
        var button_id = chart_id + "-" + name;
        d3.select(button_id).on("click", function() {
            fetch_for_ordering(order);

            /* drop off the '#' sign to convert id to a class prefix */
            d3.selectAll("." + chart_id.substring(1) + "-groupby")
                .classed("active", false);
            d3.select(button_id).classed("active", true);
        });
    };

    $.each(orderings, function(k, v) {
        make_group_button(k, v);
    });

    var resize_timeout = null;
    var real_resize = function() {
        resize_timeout = null;
        d3_div.selectAll("div")
            .data(treemap.size([jq_div.width(), jq_div.height()]), key_func)
            .call(cell);
    };
    $(window).resize(function() {
        if (resize_timeout) {
            clearTimeout(resize_timeout);
        }
        resize_timeout = setTimeout(real_resize, 200);
    });
}
